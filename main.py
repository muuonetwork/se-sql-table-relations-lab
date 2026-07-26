# STEP 0

# SQL Library and Pandas Library
import sqlite3
import pandas as pd

# Connect to the database
conn = sqlite3.connect('data.sqlite')

pd.read_sql("""SELECT * FROM sqlite_master""", conn)


# ---------------------------------------------------------------------------
# PART 1: JOIN AND FILTER
# ---------------------------------------------------------------------------

# STEP 1
# Boston employees: first/last name + job title.
# employees.officeCode -> offices.officeCode, filter offices.city = 'Boston'
df_boston = pd.read_sql("""
    SELECT e.firstName, e.jobTitle
    FROM employees AS e
    JOIN offices AS o
        ON e.officeCode = o.officeCode
    WHERE o.city = 'Boston';
""", conn)


# STEP 2
# Offices with zero employees.
# LEFT JOIN offices -> employees so offices with no matching employee keep a row
# (employeeNumber will be NULL), then filter with HAVING on the count.
df_zero_emp = pd.read_sql("""
    SELECT o.officeCode, o.city, COUNT(e.employeeNumber) AS numEmployees
    FROM offices AS o
    LEFT JOIN employees AS e
        ON o.officeCode = e.officeCode
    GROUP BY o.officeCode, o.city
    HAVING COUNT(e.employeeNumber) = 0;
""", conn)


# ---------------------------------------------------------------------------
# PART 2: TYPE OF JOIN
# ---------------------------------------------------------------------------

# STEP 3
# All employees, plus office city/state IF they have one.
# LEFT JOIN keeps every employee even if officeCode doesn't match an office.
df_employee = pd.read_sql("""
    SELECT e.firstName, e.lastName, o.city, o.state
    FROM employees AS e
    LEFT JOIN offices AS o
        ON e.officeCode = o.officeCode
    ORDER BY e.firstName, e.lastName;
""", conn)


# STEP 4
# Customers who have NOT placed an order.
# Approach: LEFT JOIN customers -> orders, keep rows where orders.orderNumber IS NULL.
df_contacts = pd.read_sql("""
    SELECT c.contactFirstName, c.contactLastName, c.phone, c.salesRepEmployeeNumber
    FROM customers AS c
    LEFT JOIN orders AS o
        ON c.customerNumber = o.customerNumber
    WHERE o.orderNumber IS NULL
    ORDER BY c.contactLastName;
""", conn)


# ---------------------------------------------------------------------------
# PART 3: BUILT-IN FUNCTION
# ---------------------------------------------------------------------------

# STEP 5
# Customer contacts + payment amount/date, sorted by amount descending.
# `amount` is stored as TEXT in this database, so a plain ORDER BY amount DESC
# sorts alphabetically (e.g. "9900.00" comes before "15000.00"). CAST fixes this.
df_payment = pd.read_sql("""
    SELECT c.contactFirstName, c.contactLastName, p.amount, p.paymentDate
    FROM customers AS c
    JOIN payments AS p
        ON c.customerNumber = p.customerNumber
    ORDER BY CAST(p.amount AS REAL) DESC;
""", conn)


# ---------------------------------------------------------------------------
# PART 4: JOINING AND GROUPING
# ---------------------------------------------------------------------------

# STEP 6
# Employees whose customers have an AVG credit limit > 90k.
# Group by employee, aggregate AVG(creditLimit), filter with HAVING (post-aggregation).
df_credit = pd.read_sql("""
    SELECT e.employeeNumber, e.firstName, e.lastName, COUNT(c.customerNumber) AS numCustomers
    FROM employees AS e
    JOIN customers AS c
        ON e.employeeNumber = c.salesRepEmployeeNumber
    GROUP BY e.employeeNumber, e.firstName, e.lastName
    HAVING AVG(c.creditLimit) > 90000
    ORDER BY numCustomers DESC;
""", conn)


# STEP 7
# Product name + number of orders (numorders) + total units sold (totalunits).
df_product_sold = pd.read_sql("""
    SELECT p.productName,
           COUNT(od.orderNumber) AS numorders,
           SUM(od.quantityOrdered) AS totalunits
    FROM products AS p
    JOIN orderdetails AS od
        ON p.productCode = od.productCode
    GROUP BY p.productCode, p.productName
    ORDER BY totalunits DESC;
""", conn)


# ---------------------------------------------------------------------------
# PART 5: MULTIPLE JOINS
# ---------------------------------------------------------------------------

# STEP 8
# Product name/code + number of DISTINCT customers who ordered each product.
# Chain: products -> orderdetails -> orders -> customers
df_total_customers = pd.read_sql("""
    SELECT p.productName, p.productCode,
           COUNT(DISTINCT o.customerNumber) AS numpurchasers
    FROM products AS p
    JOIN orderdetails AS od
        ON p.productCode = od.productCode
    JOIN orders AS o
        ON od.orderNumber = o.orderNumber
    GROUP BY p.productCode, p.productName
    ORDER BY numpurchasers DESC;
""", conn)


# STEP 9
# Number of customers per office (n_customers), with officeCode and city.
# Chain: offices -> employees -> customers
df_customers = pd.read_sql("""
    SELECT o.officeCode, o.city, COUNT(c.customerNumber) AS n_customers
    FROM offices AS o
    JOIN employees AS e
        ON o.officeCode = e.officeCode
    JOIN customers AS c
        ON e.employeeNumber = c.salesRepEmployeeNumber
    GROUP BY o.officeCode, o.city;
""", conn)


# ---------------------------------------------------------------------------
# PART 6: SUBQUERY
# ---------------------------------------------------------------------------

# STEP 10
# Employees who sold products ordered by fewer than 20 distinct customers.
# Subquery: find productCodes with COUNT(DISTINCT customerNumber) < 20.
# Outer query: join employees -> customers -> orders -> orderdetails -> products
# and filter productCode IN that subquery's results.
df_under_20 = pd.read_sql("""
    SELECT DISTINCT e.employeeNumber, e.firstName, e.lastName, o.city, o.officeCode
    FROM employees AS e
    JOIN offices AS o
        ON e.officeCode = o.officeCode
    JOIN customers AS c
        ON e.employeeNumber = c.salesRepEmployeeNumber
    JOIN orders AS ord
        ON c.customerNumber = ord.customerNumber
    JOIN orderdetails AS od
        ON ord.orderNumber = od.orderNumber
    WHERE od.productCode IN (
        SELECT od2.productCode
        FROM orderdetails AS od2
        JOIN orders AS ord2
            ON od2.orderNumber = ord2.orderNumber
        GROUP BY od2.productCode
        HAVING COUNT(DISTINCT ord2.customerNumber) < 20
    )
    ORDER BY e.lastName;
""", conn)


# Close the connection
conn.close()
