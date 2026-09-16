# Order Management Requirements

## REQ-ORD-001 Create Order
An operator shall be able to create an order for an active customer and a valid product.
An order contains a customer, product, quantity, status and calculated amount.

## REQ-ORD-002 Validate Order
An order identifier and quantity must be greater than zero before an order is accepted.
Validation logic shall be shared by create, modify and cancel flows.

## REQ-ORD-003 Modify Order
An operator shall be able to modify the quantity of an open order after validation.

## REQ-ORD-004 Cancel Order
An operator shall be able to cancel an open order. Cancellation must retain a history record
and the stock allocated to the order must be releasable by downstream batch processing.

## REQ-ORD-005 Process Orders
A batch process shall process open orders and use common lookup/database routines.
