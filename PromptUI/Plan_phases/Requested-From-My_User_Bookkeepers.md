## Here's the Request From my User/Bookkeeprs from the feature Adding Entry/Editing Entry as long related to that feature.

The user/bookkeeper is requesting a more flexible calculation feature for line items.

Requested Features
Add a calculator feature for each line item that supports:
Addition
Subtraction
Multiplication
Division
Percentage calculations
The calculations should work between specific line items only.
Example:
One line item can be subtracted from another specific line item.
A percentage can also be applied to a specific line item amount.
Example:
Sales amount = 386,000
Apply 20%
The system should display the actual calculated amount based on 20% of 386,000.
Percentage calculations should only affect and display within the selected line item.
They should NOT automatically affect the Net Value.
The current Net Value calculation logic is incorrect.
Right now, the system automatically subtracts tax-related line items from the Net Value.
This should not happen because some client taxes do not require calculations at all.
Net Value should only be affected by explicit calculations made between line items.
If no calculation is applied, the line item should not be included in the Net Value computation automatically.
Some tax line items are only informational and should remain untouched.
These should not automatically participate in calculations or Net Value deductions.
Add an indicator or visual identifier showing:
Which line items have calculations applied
Which line items are linked to other line items in calculations


## Main Goal

The system should allow manual and flexible calculations between selected line items instead of automatically calculating everything into the Net Value. The user/bookkeeper wants full control over which line items affect the Net Value and which ones are only informational or percentage-based.