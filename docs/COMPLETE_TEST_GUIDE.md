# Rajput Gas Control System - Complete Test Guide

## Overview
This comprehensive test guide ensures that all features of the Rajput Gas Control System work correctly, with special focus on the dynamic refresh functionality that updates dashboard and all modules in real-time.

## Test Environment Setup
1. **Prerequisites**: Ensure the application is installed and database is initialized
2. **Test Data**: Use provided test scripts to generate sample data
3. **User Roles**: Test with different user roles (Admin, Accountant, Gate Operator, Driver)

## 1. Authentication & User Management Tests

### 1.1 Login Functionality
**Test Steps:**
1. Launch the application
2. Enter valid admin credentials (username: `admin`, password: `admin123`)
3. Click "Login"
4. Verify successful login and dashboard appears

**Expected Results:**
- ✅ Login dialog closes
- ✅ Main window opens with dashboard
- ✅ User role-based navigation is enabled/disabled correctly

### 1.2 User Role Permissions
**Test with Different Roles:**
```
Admin: Full access to all modules
Accountant: Dashboard, Clients, Gas Products, Sales, Receipts, Reports
Gate Operator: Dashboard, Gate Passes only
Driver: Dashboard only
```

**Test Steps:**
1. Logout and login with each role
2. Verify accessible modules match role permissions
3. Verify restricted modules are disabled

## 2. Dashboard Dynamic Refresh Tests

### 2.1 Real-time Statistics Updates
**Test Steps:**
1. **Initial State**: Note dashboard statistics (Total Clients, Total Sales, Outstanding Balance, Today's Sales)
2. **Add Client**: Navigate to Clients → Add New Client → Return to Dashboard
3. **Verify**: Client count increases immediately
4. **Add Sale**: Navigate to Sales → Create New Sale → Return to Dashboard  
5. **Verify**: Sales totals update immediately

**Expected Results:**
- ✅ Dashboard statistics refresh automatically when navigating back
- ✅ All numbers update to reflect current database state
- ✅ No manual refresh required

### 2.2 Cross-Module Data Consistency
**Test Steps:**
1. Add client in Clients module
2. Navigate to Sales module
3. Verify new client appears in dropdown
4. Create sale for new client
5. Navigate to Receipts module
6. Verify sale appears for receipt creation

**Expected Results:**
- ✅ Data added in one module immediately available in others
- ✅ No stale data or inconsistencies

## 3. Client Management Tests

### 3.1 Add New Client
**Test Data:**
```
Name: "Test Client Alpha"
Phone: "+92-300-1234567"
Address: "123 Test Street, Lahore"
Company: "Test Company Ltd"
```

**Test Steps:**
1. Navigate to Clients module
2. Click "Add Client"
3. Fill all required fields
4. Click "Save"
5. Verify client appears in table
6. Navigate to Dashboard → Verify client count increased

### 3.2 Edit Client Information
**Test Steps:**
1. Select existing client from table
2. Click "Edit Client"
3. Modify phone number
4. Save changes
5. Verify updates reflect immediately

### 3.3 Client Balance Updates
**Test Steps:**
1. Create sale for test client
2. Verify balance updates in client table
3. Create receipt for partial payment
4. Verify balance decreases correctly
5. Navigate away and return → Verify balance persists

## 4. Gas Products Management Tests

### 4.1 Product Catalog Management
**Test Products:**
```
Gas Type: "Oxygen"
Sub Type: "Industrial"
Capacity: "50L"
Unit Price: 2500.00
Description: "High purity oxygen"
```

**Test Steps:**
1. Navigate to Gas Products module
2. Add new product with above details
3. Verify product appears in table
4. Navigate to Sales module → Verify product available for sale
5. Return to Gas Products → Verify data persists

### 4.2 Price Updates
**Test Steps:**
1. Edit existing product price
2. Navigate to Sales module
3. Create new sale with updated product
4. Verify new price is used in calculations

## 5. Sales & Billing Tests

### 5.1 Create Complete Sale Transaction
**Test Steps:**
1. Navigate to Sales module
2. Select existing client
3. Select gas product
4. Enter quantity: 5
5. Verify automatic calculations (subtotal, tax, total)
6. Enter amount paid: partial payment
7. Complete sale
8. Navigate to Dashboard → Verify sales statistics updated

### 5.2 Sales Receipt Generation
**Test Steps:**
1. After creating sale, navigate to Receipts module
2. Find the new sale in pending receipts
3. Generate receipt
4. Verify receipt number is auto-generated
5. Navigate to Reports → Verify sale appears in reports

### 5.3 Multi-Product Sale
**Test Steps:**
1. Create sale with multiple gas products
2. Verify total calculations are correct
3. Generate single receipt for entire sale
4. Verify all products appear on receipt

## 6. Receipts & Payment Tracking Tests

### 6.1 Payment Recording
**Test Steps:**
1. Navigate to Receipts module
2. Select pending sale
3. Record partial payment
4. Navigate to Clients → Verify balance updated
5. Navigate to Dashboard → Verify outstanding balance updated

### 6.2 Receipt Numbering
**Test Steps:**
1. Create multiple receipts
2. Verify receipt numbers are sequential
3. Check format: `RCP-2024-000001`, `RCP-2024-000002`
4. Restart application → Verify numbering continues correctly

## 7. Gate Pass Management Tests

### 7.1 Gate Pass Creation
**Test Data:**
```
Driver Name: "Muhammad Ali"
Vehicle Number: "LEB-1234"
Gas Type: "Oxygen"
Capacity: "50L"
Quantity: 3
```

**Test Steps:**
1. Navigate to Gate Passes module
2. Select valid receipt
3. Enter driver and vehicle information
4. Generate gate pass
5. Verify gate pass number format: `GP-2024-000001`
6. Record time out

### 7.2 Gate Pass Return
**Test Steps:**
1. When vehicle returns, find gate pass
2. Record time in
3. Verify gate pass status updated
4. Navigate to Reports → Verify gate pass activity

## 8. Employee Management Tests

### 8.1 Employee Records
**Test Steps:**
1. Navigate to Employees module
2. Add new employee record
3. Verify employee appears in table
4. Edit employee salary information
5. Verify updates persist after navigation

### 8.2 Role-Based Access
**Test Steps:**
1. Create employee with "Gate Operator" role
2. Login as that employee
3. Verify only Dashboard and Gate Passes are accessible
4. Verify other modules are disabled

## 9. Reports & Analytics Tests

### 9.1 Sales Reports
**Test Steps:**
1. Navigate to Reports module
2. Select date range (last 30 days)
3. Generate sales report
4. Verify totals match dashboard statistics
5. Export report to PDF/Excel
6. Verify data consistency

### 9.2 Client Statements
**Test Steps:**
1. Select specific client
2. Generate client statement
3. Verify all transactions appear
4. Verify balance calculations are correct
5. Navigate to other modules → Return to Reports → Verify data persists

## 10. Settings & Configuration Tests

### 10.1 Application Settings
**Test Steps:**
1. Navigate to Settings module
2. Modify company information
3. Change tax rates
4. Save settings
5. Navigate away and return → Verify settings persist
6. Create new sale → Verify new tax rates applied

### 10.2 User Preferences
**Test Steps:**
1. Change theme/settings if available
2. Logout and login → Verify preferences maintained
3. Restart application → Verify settings persist

## 11. Data Persistence Tests

### 11.1 Application Restart
**Test Steps:**
1. Add test data in all modules
2. Close application completely
3. Restart application
4. Login and navigate to all modules
5. Verify all test data persists
6. Verify dashboard statistics are accurate

### 11.2 Database Integrity
**Test Steps:**
1. Run the provided test script: `python test_dynamic_refresh.py`
2. Verify all tests pass
3. Check database file exists and is accessible
4. Verify backup functionality works

## 12. Performance & Load Tests

### 12.1 Large Dataset Handling
**Test Steps:**
1. Add 50+ clients
2. Create 100+ sales transactions
3. Generate reports with large datasets
4. Verify application remains responsive
5. Check dashboard refresh time < 2 seconds

### 12.2 Concurrent Operations
**Test Steps:**
1. Rapidly switch between modules
2. Create multiple transactions quickly
3. Verify no data corruption or conflicts
4. Check all refreshes complete successfully

## 13. Error Handling Tests

### 13.1 Invalid Data Entry
**Test Steps:**
1. Try to save client without required fields
2. Enter negative quantities in sales
3. Try to create sale for non-existent client
4. Verify appropriate error messages appear
5. Verify application doesn't crash

### 13.2 Database Connection Issues
**Test Steps:**
1. Test with database file locked/missing
2. Verify graceful error handling
3. Check error messages are user-friendly

## 14. Integration Test Scenarios

### 14.1 Complete Business Flow
**Test Complete Transaction Flow:**
1. Add new client
2. Add new gas product
3. Create sale for client
4. Generate receipt
5. Create gate pass
6. Record gate pass return
7. Generate reports
8. Verify all data is consistent across modules

### 14.2 Month-End Process
**Test Steps:**
1. Generate monthly sales report
2. Verify all transactions included
3. Check client balance statements
4. Generate gate pass activity report
5. Verify data integrity across all reports

## Test Completion Checklist

- [ ] All modules accessible and functional
- [ ] Dashboard updates automatically with changes
- [ ] Data persists after application restart
- [ ] User role permissions work correctly
- [ ] All CRUD operations work properly
- [ ] Reports generate accurately
- [ ] Error handling works appropriately
- [ ] Performance is acceptable (< 2 second refresh)
- [ ] Database integrity maintained
- [ ] All test scripts pass successfully

## Post-Test Actions

1. **Cleanup**: Remove test data if desired
2. **Backup**: Create final backup of clean database
3. **Documentation**: Record any issues found
4. **Sign-off**: Mark test phase complete

## Support

If any tests fail or issues are encountered:
1. Check the error logs in the application
2. Verify database connectivity
3. Run the diagnostic test script
4. Review the implementation in main_window.py for refresh functionality

**Test Guide Version**: 1.0
**Last Updated**: November 2024
**Application Version**: 1.0