# Rajput Gas Management System - Manual Testing Guide

## 🚀 Application Startup Test

### Test 1: Application Launch
**Steps:**
1. Open terminal in project directory
2. Run command: `py main.py`
3. Observe application startup

**Expected Result:**
- Application opens without errors
- Login dialog appears
- No console errors displayed

---

## 🔐 Authentication Testing

### Test 2: User Login
**Steps:**
1. Enter username: `admin` 
2. Enter password: `admin123`
3. Click "Login" button

**Expected Result:**
- Successfully logged in
- Dashboard opens showing statistics
- User name displayed in status bar

### Test 3: Invalid Login
**Steps:**
1. Enter invalid username/password
2. Click "Login" button

**Expected Result:**
- Error message displayed
- Cannot access application
- Login dialog remains open

---

## 📊 Dashboard Testing

### Test 4: Dashboard Statistics
**Steps:**
1. Login to application
2. Observe dashboard statistics cards:
   - Total Clients
   - Total Products
   - Total Sales
   - Total Revenue

**Expected Result:**
- All statistics display correct numbers
- Cards are properly formatted
- No empty or zero values (unless database is empty)

### Test 5: Dashboard Dynamic Refresh
**Steps:**
1. Note current dashboard statistics
2. Navigate to Clients module
3. Add a new client
4. Return to Dashboard

**Expected Result:**
- Client count increases by 1
- Dashboard automatically refreshes
- Changes reflect immediately

---

## 👥 Client Management Testing

### Test 6: Add New Client
**Steps:**
1. Click "Clients" in navigation
2. Click "Add Client" button
3. Fill in client details:
   - Name: `Test Client`
   - Phone: `0300-1234567`
   - Company: `Test Company`
   - Address: `123 Test Street`
4. Click "Save"

**Expected Result:**
- Client added successfully
- Client appears in client list
- Success message displayed

### Test 7: Edit Client
**Steps:**
1. Select a client from the list
2. Click "Edit Client" button
3. Modify client details
4. Click "Update"

**Expected Result:**
- Client details updated
- Changes reflected in list
- Success message displayed

### Test 8: Delete Client
**Steps:**
1. Select a client from the list
2. Click "Delete Client" button
3. Confirm deletion

**Expected Result:**
- Client removed from list
- Confirmation message displayed
- Dashboard client count updates

---

## 🛢️ Gas Products Testing

### Test 9: Add Gas Product
**Steps:**
1. Click "Gas Products" in navigation
2. Click "Add Product" button
3. Fill product details:
   - Gas Type: `Oxygen`
   - Sub Type: `Industrial`
   - Capacity: `50L`
   - Price: `1500`
   - Stock Quantity: `100`
4. Click "Save"

**Expected Result:**
- Product added successfully
- Product appears in product list
- Dashboard product count increases

### Test 10: Update Product Stock
**Steps:**
1. Select a product from list
2. Click "Edit Product" button
3. Change stock quantity
4. Click "Update"

**Expected Result:**
- Stock quantity updated
- Changes reflected immediately
- Dashboard updates if applicable

---

## 💰 Sales Testing

### Test 11: Create New Sale
**Steps:**
1. Click "Sales" in navigation
2. Click "New Sale" button
3. Select client from dropdown
4. Add products to sale:
   - Select product
   - Enter quantity
   - Click "Add Product"
5. Verify sale details
6. Click "Complete Sale"

**Expected Result:**
- Sale created successfully
- Receipt generated automatically
- Sale appears in recent sales list
- Dashboard sales count and revenue update

### Test 12: Generate Receipt for Sale
**Steps:**
1. Go to "Recent Sales" tab
2. Select a sale from the list
3. Click "Generate Receipt for Selected"

**Expected Result:**
- Receipt dialog opens
- Receipt shows correct details:
  - Client information
  - Product details
  - Sale amounts
  - Cashier name (this was the bug we fixed)
- Receipt can be printed

### Test 13: Verify Receipt Details
**Check these fields on the receipt:**
- Client name and contact info
- Product details (gas type, capacity)
- Quantity and unit price
- Subtotal, tax, and total amounts
- **Cashier name** (critical - this was the bug)
- Receipt date and time

**Expected Result:**
- All fields populated correctly
- No missing information
- Receipt format is professional

---

## 📄 Receipts Module Testing

### Test 14: View All Receipts
**Steps:**
1. Click "Receipts" in navigation
2. Observe receipts list

**Expected Result:**
- All receipts displayed
- Receipt details visible
- Can search/filter receipts

### Test 15: Receipt Search
**Steps:**
1. Use search functionality
2. Search by client name or receipt number

**Expected Result:**
- Search returns correct results
- Filters work properly

---

## 🚪 Gate Passes Testing

### Test 16: Create Gate Pass
**Steps:**
1. Click "Gate Passes" in navigation
2. Click "New Gate Pass" button
3. Fill required details:
   - Select sale/receipt
   - Vehicle number
   - Driver name
   - Expected time
4. Click "Generate Gate Pass"

**Expected Result:**
- Gate pass created successfully
- Gate pass appears in list
- Can print gate pass

---

## 👨‍💼 Employees Testing

### Test 17: Add Employee
**Steps:**
1. Click "Employees" in navigation
2. Click "Add Employee" button
3. Fill employee details:
   - Full name
   - Username
   - Password
   - Role (Admin/Cashier)
4. Click "Save"

**Expected Result:**
- Employee added successfully
- Can login with new credentials
- Employee appears in list

---

## 📈 Reports Testing

### Test 18: Generate Sales Report
**Steps:**
1. Click "Reports" in navigation
2. Select date range
3. Click "Generate Sales Report"

**Expected Result:**
- Report generated successfully
- Shows correct sales data
- Can export/print report

### Test 19: Generate Stock Report
**Steps:**
1. In Reports module
2. Click "Stock Report" tab
3. Generate stock report

**Expected Result:**
- Current stock levels displayed
- Low stock items highlighted
- Report is accurate

---

## ⚙️ Settings Testing

### Test 20: Application Settings
**Steps:**
1. Click "Settings" in navigation
2. Modify any settings
3. Click "Save Settings"

**Expected Result:**
- Settings saved successfully
- Changes applied immediately

---

## 🔄 Data Persistence Testing

### Test 21: Data Persistence Across Restarts
**Steps:**
1. Add some test data (clients, products, sales)
2. Note current statistics
3. Close application completely
4. Restart application
5. Login again
6. Check dashboard and all modules

**Expected Result:**
- All data preserved
- Statistics remain the same
- No data loss occurred
- Dashboard reflects previous data

---

## 🔄 Dynamic Refresh Testing

### Test 22: Cross-Module Data Synchronization
**Steps:**
1. Open application in one window
2. Note current dashboard stats
3. Create a new sale
4. Check dashboard immediately
5. Navigate between different modules
6. Observe if data updates everywhere

**Expected Result:**
- Dashboard updates automatically
- All modules show synchronized data
- No manual refresh needed
- Real-time data consistency

---

## 🐛 Error Handling Testing

### Test 23: Invalid Data Entry
**Steps:**
1. Try to save forms with empty required fields
2. Enter invalid phone numbers
3. Try negative quantities for sales

**Expected Result:**
- Appropriate error messages displayed
- Forms don't submit with invalid data
- Data validation works properly

---

## ✅ Final Verification Checklist

After completing all tests, verify:

- [ ] Application starts without errors
- [ ] Login works correctly
- [ ] Dashboard shows real-time updates
- [ ] All CRUD operations work (Create, Read, Update, Delete)
- [ ] Receipt generation includes cashier name
- [ ] Data persists after app restart
- [ ] Dynamic refresh works across modules
- [ ] No console errors during operation
- [ ] All buttons and navigation work
- [ ] Reports generate correctly

---

## 📝 Test Data Cleanup

After testing:
1. Delete test clients, products, and sales
2. Verify dashboard updates after cleanup
3. Ensure application is ready for production use

---

**Note:** This testing guide covers the complete functionality of your Rajput Gas Management System. Each test verifies a specific feature and ensures the application works as expected. The dynamic refresh functionality and data persistence are key features to test thoroughly.