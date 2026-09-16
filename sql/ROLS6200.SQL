-- Logical batch SQL artifact, intentionally separate like legacy ROLLS SQL scripts.
SELECT o.ORDER_ID, ol.PRODUCT_ID, ol.QUANTITY
FROM ORDERS o
JOIN ORDER_LINE ol ON ol.ORDER_ID = o.ORDER_ID
WHERE o.STATUS = 'OPEN';
