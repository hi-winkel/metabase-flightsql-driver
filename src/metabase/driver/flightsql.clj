(ns metabase.driver.flightsql
  "Arrow Flight SQL Driver for Metabase.

  This driver uses the Apache Arrow Flight SQL JDBC driver.
  ...
  "
  (:require
   ;; String manipulation functions.
   [clojure.string :as str]
   ;; JDBC library for database connectivity.
   [clojure.java.jdbc :as jdbc]
   ;; URL encoding/decoding utilities.
   [ring.util.codec :as codec]
   ;; Core Metabase driver functionality.
   [metabase.driver :as driver]
   ;; Common functions for Metabase drivers.
   [metabase.driver.common :as driver.common]
   ;; SQL generation and manipulation.
   [honey.sql :as sql]
   ;; Metabase SQL-JDBC integration.
   [metabase.driver.sql-jdbc :as sql-jdbc]
   ;; Common functions for SQL-JDBC drivers.
   [metabase.driver.sql-jdbc.common :as sql-jdbc.common]
   ;; Connection management for SQL-JDBC drivers.
   [metabase.driver.sql-jdbc.connection :as sql-jdbc.conn]
   ;; Logging utilities.
   [metabase.util.log :as log]
   ;; SQL query processing.
   [metabase.driver.sql.query-processor :as sql.qp]
   ;; Schema synchronization for SQL-JDBC drivers.
   [metabase.driver.sql-jdbc.sync :as sql-jdbc.sync]
   ;; SQL execution helper functions.
   [metabase.driver.sql-jdbc.execute :as sql-jdbc.execute]
   ))

;; ----------------------------------------------------------------
;; Register this driver as a JDBC-based driver with parent :sql-jdbc.
(driver/register! :arrow-flight-sql, :parent #{:sql-jdbc})

;; ----------------------------------------------------------------
;; Define the display name for the Arrow Flight SQL driver.
(defmethod driver/display-name :arrow-flight-sql [_]
  "Arrow Flight SQL")

;; ----------------------------------------------------------------
;; Register feature support flags for the driver.
;; This loop defines which features the driver supports.
(doseq [[feature supported?]
        {:describe-fields           true
         :connection-impersonation  false
         :convert-timezone          true}]
  (defmethod driver/database-supports? [:arrow-flight-sql feature]
    [_driver _feature _db]
    supported?))

;; ----------------------------------------------------------------
;; Helper function that returns the string if it is non-blank;
;; otherwise, it returns the provided default value.
(defn non-blank [s default]
  (if (and (string? s) (not (str/blank? s)))
    s
    default))

;; ----------------------------------------------------------------
;; Build a connection spec from the provided database details.
;; This constructs a JDBC connection specification map for Arrow Flight SQL.
;; ----------------------------------------------------------------
(defmethod sql-jdbc.conn/connection-details->spec :arrow-flight-sql
  [_ details]
  (let [{:keys [host port token useEncryption disableCertificateVerification]
         :or   {useEncryption true
                disableCertificateVerification false}} details
        ;; URI-encode _only_ the raw token
        enc-token (when (and (string? token)
                             (not (str/blank? token)))
                    (codec/url-encode token))
        ;; Manually assemble each key=value pair
        params    (cond-> []
                    enc-token    (conj (str "authorization=Bearer%20" enc-token))
                    true         (conj (str "useEncryption=" useEncryption))
                    true         (conj (str "disableCertificateVerification="
                                            disableCertificateVerification)))
        qp         (str/join "&" params)
        ;; Build the full JDBC URI exactly as DBeaver would expect
        full-url   (str "jdbc:arrow-flight-sql://"
                        (or host "localhost")
                        ":"
                        (or port 443)
                        (when-not (str/blank? qp) (str "?" qp)))]
    ;; Now split it into subprotocol + subname for the JDBC spec
    (let [scheme     "jdbc:arrow-flight-sql:"
          subname    (subs full-url (count scheme))]
      (-> {:classname   "org.apache.arrow.driver.jdbc.ArrowFlightJdbcDriver"
           :subprotocol "arrow-flight-sql"
           :subname     subname
           :cast        (fn [col val]
                          (if (and (= (:base-type col) :type/DateTime)
                                   (instance? java.sql.Timestamp val))
                            (.toLocalDateTime ^java.sql.Timestamp val)
                            val))}
))))





;; ----------------------------------------------------------------
;; Test the connection to the Arrow Flight SQL database.
;; Executes a simple "SELECT 1" query to verify connectivity.
(defmethod driver/can-connect? :arrow-flight-sql
  [driver details]
  (try
    (sql-jdbc.conn/with-connection-spec-for-testing-connection [spec [driver details]]
      (jdbc/query spec "SELECT 1"))
    true
    (catch Exception e
      (log/error e "Flight SQL connection test failed.")
      false)))

;; ----------------------------------------------------------------
;; Map raw database types to Metabase base types.
;; This converts a database-specific type into a standardized Metabase type.
(def ^:private database-type->base-type
  (sql-jdbc.sync/pattern-based-database-type->base-type
   [[#"BOOL"                       :type/Boolean]
    [#"INT(8|16|32|64)?$"          :type/Integer]
    [#"UINT(8|16|32)$"             :type/Integer]
    [#"UINT64"                     :type/BigInteger]
    [#"BIGINT|HUGEINT"             :type/BigInteger]
    [#"FLOAT(16|32|64)?$"          :type/Float]
    [#"DOUBLE|REAL"                :type/Float]
    [#"DECIMAL|NUMERIC"            :type/Decimal]
    [#"DATE32|DATE"                :type/Date]
    [#"TIME(32|64)?$"              :type/Time]
    [#"TIMESTAMP"                  :type/DateTime]
    [#"UTF8|CHAR|STRING|TEXT|VARCHAR" :type/Text]
    [#"JSON"                       :type/JSON]
    [#"UUID"                       :type/UUID]
    ;; fallback for anything else
    [#".*"                         :type/*]]))

(defmethod sql-jdbc.sync/database-type->base-type :arrow-flight-sql
  [_ raw-db-type]
  ;; strip off any precision/scale qualifiers, e.g. "DECIMAL(10,2)" → "DECIMAL"
  (let [normalized (-> raw-db-type
                       (str/replace #"\(.*\)" "")
                       str/upper-case)]
    (database-type->base-type normalized)))


;; ----------------------------------------------------------------
;; Define a reader function for TIMESTAMP columns.
;; Retrieves a timestamp from the ResultSet and converts it to a local date-time.
(defmethod sql-jdbc.execute/read-column-thunk [:arrow-flight-sql java.sql.Types/TIMESTAMP]
  [_driver ^java.sql.ResultSet rs _rsmeta ^Integer i]
  (fn []
    (some-> (.getTimestamp rs i)
            .toLocalDateTime)))

;; ----------------------------------------------------------------
;; Custom Schema Sync Implementations
;; ----------------------------------------------------------------

;; List tables by executing the "SHOW TABLES" command.
(defmethod driver/describe-database :arrow-flight-sql
  [driver database]
  (let [spec (sql-jdbc.conn/connection-details->spec :arrow-flight-sql (:details database))]
    (with-open [conn (jdbc/get-connection spec)]
      (let [rows (jdbc/query {:connection conn}
                             ["SHOW TABLES"]
                             {:identifiers str/lower-case})
            formatted (->> rows
                           (filter #(not= (str/lower-case (:table_schema %)) "information_schema"))
                           (map (fn [row]
                                  {:name   (:table_name row)
                                   :schema (:table_schema row)})))]
        {:tables (into #{} formatted)})))) ;; Return a set of formatted table information

;; ----------------------------------------------------------------
;; Describe a specific table by executing a DESCRIBE query.
(defmethod driver/describe-table :arrow-flight-sql
  [_ driver database {:keys [name schema]}]
  (let [spec (sql-jdbc.conn/connection-details->spec :arrow-flight-sql (:details database))]
    (with-open [conn (jdbc/get-connection spec)]
      (let [query   (format "DESCRIBE \"%s\".\"%s\"" schema name) ;; Build the DESCRIBE query using schema and table name
            results (jdbc/query {:connection conn} [query] {:identifiers str/lower-case})
            fields  (mapv (fn [{:keys [column_name data_type is_nullable]}]
                            (let [normalized-name (-> column_name
                                                      (str/replace #"^\"|\"$" "")
                                                      str/lower-case)]
                              {:name          normalized-name
                               :database-type data_type
                               :base-type     (sql-jdbc.sync/database-type->base-type driver data_type)
                               :nullable      (= "yes" (str/lower-case is_nullable))
                               :field-comment ""}))   ;; Default comment placeholder for each field
                          results)]
        (log/info "DESCRIBE query:" query)
        (log/info "DESCRIBE raw results:" results)
        (log/info "Parsed fields:" fields)
        {:name name
         :schema schema
         :fields fields}))))

;; ----------------------------------------------------------------
;; Define a method to describe table foreign keys.
;; Since FlightSQL does not support imported keys, this returns an empty set.
(defmethod driver/describe-table-fks :arrow-flight-sql
  [_ _ _]
  ;; Return an empty set so that foreign key synchronization doesn't fail.
  #{})

;; ----------------------------------------------------------------
;; Describe fields by querying the information_schema.columns table.
;; Builds a dynamic SQL query based on provided schema and table names.
(defmethod sql-jdbc.sync/describe-fields-sql :arrow-flight-sql
  [driver & {:keys [schema-names table-names details]}]
  (let [base-condition [:>= [:inline 1] [:inline 1]]
        schema-condition (when (seq schema-names)
                           [:in [:lower :table_schema]
                            (mapv (fn [s] [:inline (str/lower-case s)]) schema-names)])
        table-condition (when (seq table-names)
                          [:in [:lower :table_name]
                           (mapv (fn [t] [:inline (str/lower-case t)]) table-names)])
        where-clause (cond-> [base-condition]
                       schema-condition (conj schema-condition)
                       table-condition (conj table-condition))]
    (sql/format
     {:select [[:column_name :name]
               [:ordinal_position :database-position]
               [:table_schema :table-schema]
               [:table_name :table-name]
               [[[:upper :data_type]] :database-type]
               [[:inline false] :database-is-auto-increment]
               [[:case-expr [:= :is_nullable [:inline "NO"]] [:inline true] [:inline false]]
                :database-required]
               [[:inline ""] :field-comment]]
      :from [[:information_schema.columns]]
      :where (vec (cons :and where-clause))
      :order-by [:table_schema :table_name :ordinal_position]}
     :dialect (sql.qp/quote-style driver))))
