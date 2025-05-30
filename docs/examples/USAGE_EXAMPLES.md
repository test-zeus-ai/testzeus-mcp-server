# TestZeus MCP Server - Usage Examples

This document provides practical examples of using the TestZeus MCP Server with Claude Desktop and Cursor IDE.

## Quick Setup Examples

### Claude Desktop Configuration

#### macOS Configuration

1. **Locate the configuration file:**
   ```bash
   open ~/Library/Application\ Support/Claude/
   ```

2. **Edit `claude_desktop_config.json`:**
   ```json
   {
     "mcpServers": {
       "testzeus": {
         "command": "testzeus-mcp-server",
         "args": [],
         "env": {
           "TESTZEUS_EMAIL": "john.doe@company.com",
           "TESTZEUS_PASSWORD": "your-secure-password",
           "TESTZEUS_BASE_URL": "https://api.testzeus.com"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop**

#### Windows Configuration

1. **Open the configuration directory:**
   ```cmd
   explorer %APPDATA%\Claude
   ```

2. **Same JSON configuration as above**

### Cursor IDE Configuration

1. **Open Cursor Settings** (`Ctrl/Cmd + ,`)
2. **Navigate to:** Extensions → Model Context Protocol
3. **Add new server:**

   ```json
   {
     "name": "TestZeus",
     "command": "testzeus-mcp-server",
     "args": [],
     "env": {
       "TESTZEUS_EMAIL": "john.doe@company.com",
       "TESTZEUS_PASSWORD": "your-secure-password",
       "TESTZEUS_BASE_URL": "https://api.testzeus.com"
     }
   }
   ```

## Real-World Usage Examples

### Example 1: Test Discovery and Exploration

**User:** "What tests do I have in my TestZeus account?"

**Claude Response:**
```
I'll check your TestZeus tests for you.

Based on your TestZeus account, you have 15 tests:

1. **Login Flow Test** (test://login-001)
   - Status: Active
   - Tags: authentication, critical
   - Last run: 2 days ago

2. **Registration Test** (test://reg-001)
   - Status: Active  
   - Tags: authentication, user-management
   - Last run: 1 week ago

3. **Payment Processing** (test://pay-001)
   - Status: Active
   - Tags: payment, critical, e2e
   - Last run: 3 days ago

4. **Admin Dashboard** (test://admin-001)
   - Status: Inactive
   - Tags: admin, dashboard
   - Last run: 2 weeks ago

...

Would you like me to show details for any specific test?
```

**Follow-up:** "Show me details of the login flow test"

**Claude Response:**
```
Here are the details for your Login Flow Test:

**Test ID:** login-001
**Name:** Login Flow Test
**Description:** End-to-end test for user authentication flow
**Status:** Active
**Created:** 2024-01-15
**Last Modified:** 2024-01-20

**Tags:** authentication, critical, smoke

**Test Steps:**
1. Navigate to login page
2. Enter valid credentials
3. Click login button
4. Verify successful redirect to dashboard
5. Verify user profile is loaded

**Environment:** staging
**Browser:** Chrome
**Expected Duration:** 2-3 minutes

**Recent Results:**
- Success Rate: 95% (19/20 last runs)
- Average Duration: 2.1 minutes
- Last Failure: 2024-01-18 (timeout issue)

Would you like me to run this test or check its recent results?
```

### Example 2: Creating and Managing Tests

**User:** "I need to create a test for our new checkout process"

**Claude Response:**
```
I'll help you create a test for the checkout process. Let me gather some information first.

Could you provide:
1. What specific steps should the test cover?
2. Any particular browsers or environments to test?
3. Should this be tagged in any specific way?

Or I can create a standard checkout test with common steps. Which would you prefer?
```

**User:** "Create a standard e-commerce checkout test with payment validation"

**Claude Response:**
```
I've created a comprehensive checkout test for you:

**Test Created Successfully!**

**Test ID:** checkout-e2e-001
**Name:** E-commerce Checkout Process Test
**Status:** Active

**Test Steps:**
1. Add product to cart
2. Navigate to checkout
3. Enter shipping information
4. Select payment method
5. Enter payment details
6. Review order summary
7. Complete purchase
8. Verify confirmation page
9. Verify email confirmation

**Configuration:**
- Environment: staging
- Browser: Chrome, Firefox
- Tags: e-commerce, checkout, payment, critical
- Expected Duration: 5-7 minutes

**Next Steps:**
- The test is ready to run
- You can modify steps if needed
- Would you like me to run it now or schedule it?

Test URL: test://checkout-e2e-001
```

### Example 3: Running Tests and Monitoring Results

**User:** "Run all my critical tests"

**Claude Response:**
```
I'll run all tests tagged as 'critical' for you.

**Found 5 critical tests:**
1. Login Flow Test
2. Payment Processing  
3. User Registration
4. Admin Authentication
5. E-commerce Checkout Process

**Starting test runs...**

✅ Login Flow Test - PASSED (2.1 min)
✅ Payment Processing - PASSED (4.2 min)  
✅ User Registration - PASSED (3.1 min)
❌ Admin Authentication - FAILED (timeout after 5 min)
⏳ E-commerce Checkout Process - RUNNING...

**Results Summary:**
- 3/4 completed tests PASSED
- 1 test FAILED (Admin Authentication)
- 1 test still running

**Failed Test Details:**
Admin Authentication failed due to timeout. The login page took too long to load.

Would you like me to:
1. Re-run the failed test?
2. Check the test environment status?
3. Show detailed failure logs?
```

### Example 4: Test Environment Management

**User:** "What test environments do I have available?"

**Claude Response:**
```
Here are your available test environments:

**1. Staging Environment** (environment://staging-001)
   - URL: https://staging.myapp.com
   - Status: Active
   - Browser Support: Chrome, Firefox, Safari
   - Last Updated: 2024-01-20
   - Active Tests: 12

**2. Development Environment** (environment://dev-001)
   - URL: https://dev.myapp.com  
   - Status: Active
   - Browser Support: Chrome only
   - Last Updated: 2024-01-22
   - Active Tests: 8

**3. Production Mirror** (environment://prod-mirror-001)
   - URL: https://mirror.myapp.com
   - Status: Maintenance
   - Browser Support: Chrome, Firefox
   - Last Updated: 2024-01-18
   - Active Tests: 0 (paused for maintenance)

**4. Mobile Testing** (environment://mobile-001)
   - URL: https://mobile.myapp.com
   - Status: Active
   - Device Support: iOS, Android
   - Last Updated: 2024-01-21
   - Active Tests: 6

Which environment would you like to work with?
```

### Example 5: Analyzing Test Results and Trends

**User:** "Show me the performance trends for my tests over the last month"

**Claude Response:**
```
Here's your test performance analysis for the last 30 days:

**Overall Metrics:**
- Total Test Runs: 234
- Success Rate: 87.2% (204 passed, 30 failed)
- Average Test Duration: 3.4 minutes
- Most Active Test: Login Flow (45 runs)

**Success Rate Trends:**
Week 1: 91% success rate
Week 2: 89% success rate  
Week 3: 85% success rate
Week 4: 83% success rate

⚠️ **Declining trend detected!**

**Top Failing Tests:**
1. Admin Authentication - 12 failures (timeout issues)
2. Payment Processing - 8 failures (API connection)
3. Mobile Checkout - 6 failures (element not found)
4. User Profile Update - 4 failures (validation errors)

**Performance Issues:**
- Average test duration increased by 23% this month
- Staging environment response time up 15%
- 3 tests consistently timing out

**Recommendations:**
1. Investigate staging environment performance
2. Update timeout settings for admin tests
3. Review payment API integration
4. Update mobile test selectors

Would you like me to:
- Create a detailed report?
- Schedule diagnostic tests?
- Update timeout configurations?
```

## Advanced Usage Patterns

### Test Automation Workflows

**User:** "Set up automated testing for our CI/CD pipeline"

**Claude Response:**
```
I'll help you set up automated testing for CI/CD. Here's what I can configure:

**Available Automation Options:**

1. **Trigger Tests on Code Deploy**
   - Run smoke tests after each deployment
   - Full regression suite on release branches
   - Immediate failure notifications

2. **Scheduled Test Runs**
   - Daily health checks
   - Weekly full regression
   - Monthly performance baselines

3. **Environment Monitoring**
   - Continuous uptime checks
   - Performance threshold alerts
   - Automatic issue detection

Which automation pattern interests you most? I can create the configuration and show you how to integrate it with your existing pipeline.
```

### Team Collaboration

**User:** "Share test results with my development team"

**Claude Response:**
```
I'll help you share test results with your team. Here are the options:

**Test Results Summary for Dev Team:**

**Latest Test Run Report (2024-01-22 14:30 UTC)**
- Build: release-2.1.0-rc1
- Environment: staging
- Total Tests: 23
- Passed: 21 ✅
- Failed: 2 ❌
- Duration: 47 minutes

**Failed Tests Requiring Attention:**
1. **User Profile Update** - Validation error on new email format
   - Assigned to: Backend team
   - Priority: High
   - Fix needed before release

2. **Mobile Navigation** - Element selector outdated  
   - Assigned to: Frontend team
   - Priority: Medium
   - Known issue, fix in progress

**Performance Notes:**
- All tests completed within acceptable time limits
- No new performance regressions detected
- Staging environment stable

**Next Actions:**
- Rerun failed tests after fixes
- Deploy to production once all tests pass
- Schedule release validation suite

I can format this as:
- Slack message
- Email report  
- Jira ticket updates
- GitHub PR comments

Which format would you prefer?
```

## Troubleshooting Examples

### Connection Issues

**User:** "I'm getting authentication errors"

**Claude Response:**
```
Let me help you troubleshoot the authentication issue.

**Checking your configuration...**

I see the issue. Let me verify a few things:

1. **Email format:** ✅ Looks correct
2. **Password:** ❌ May contain special characters causing issues
3. **Base URL:** ✅ Correct API endpoint
4. **Account status:** Checking...

**Troubleshooting Steps:**

1. **Try resetting your password:**
   - Go to TestZeus dashboard
   - Use "Forgot Password" option
   - Update your MCP configuration with new password

2. **Check account status:**
   - Verify your TestZeus subscription is active
   - Ensure API access is enabled

3. **Update configuration:**
   ```json
   "env": {
     "TESTZEUS_EMAIL": "your-email@domain.com",
     "TESTZEUS_PASSWORD": "new-password-here",
     "TESTZEUS_BASE_URL": "https://api.testzeus.com"
   }
   ```

4. **Restart your MCP client** after configuration changes

Would you like me to test the connection once you've updated your credentials?
```

### Test Failures

**User:** "My checkout test keeps failing, can you help debug it?"

**Claude Response:**
```
I'll help you debug the checkout test failure. Let me analyze the recent runs:

**Checkout Test Analysis (test://checkout-e2e-001)**

**Recent Failure Pattern:**
- Last 5 runs: 4 failures, 1 success
- Failure Point: Step 5 (Enter payment details)
- Error: "Element not found: #payment-card-number"

**Detailed Failure Analysis:**

**Most Recent Failure (2024-01-22 15:30):**
```
Step 4: ✅ Select payment method - PASSED
Step 5: ❌ Enter payment details - FAILED
  Error: ElementNotFoundError
  Selector: #payment-card-number
  Timeout: 10 seconds
  Screenshot: failure_20240122_1530.png
```

**Possible Causes:**
1. **UI Changes:** Payment form may have been updated
2. **Loading Time:** Element loads slower than expected  
3. **Environment Issues:** Staging payment service problems
4. **Selector Changes:** ID attribute may have changed

**Recommended Fixes:**

1. **Update Selector Strategy:**
   - Check current page HTML
   - Use more robust selectors (data-testid)
   - Add wait conditions

2. **Increase Timeout:**
   - Change from 10s to 30s for payment steps
   - Add explicit wait for element visibility

3. **Add Debugging Steps:**
   - Screenshot before payment step
   - Log current page elements
   - Verify payment service status

Would you like me to:
- Update the test with more robust selectors?
- Increase timeout values?
- Add debugging steps?
- Check other payment-related tests?
```

## Integration Examples

### Cursor IDE Workflow

**In Cursor, while coding:**

**User:** "I just modified the login component, can you test it?"

**Claude in Cursor:**
```
I'll run the login-related tests to verify your changes.

**Running Login Tests:**

1. **Login Flow Test** - Testing basic authentication
   ⏳ Running... 
   ✅ PASSED (2.3 minutes)
   
2. **Login Validation Test** - Testing error handling
   ⏳ Running...
   ✅ PASSED (1.8 minutes)

3. **Multi-Device Login** - Testing responsive design
   ⏳ Running...
   ✅ PASSED (3.1 minutes)

**Results Summary:**
All 3 login tests PASSED! 🎉

Your login component changes look good. The tests verify:
- Basic authentication flow works
- Error messages display correctly  
- Responsive design is maintained
- Performance hasn't regressed

**Code Quality Notes:**
- No new accessibility issues detected
- Login performance improved by 200ms
- All validation rules working as expected

Your changes are ready for code review!
```

### Claude Desktop Research

**User:** "I'm planning a new feature and need to understand our current test coverage"

**Claude Response:**
```
I'll analyze your current test coverage to help with feature planning.

**Current Test Coverage Analysis:**

**By Feature Area:**
- Authentication: 85% coverage (6 tests)
- User Management: 70% coverage (4 tests)  
- Payment Processing: 90% coverage (8 tests)
- Admin Functions: 45% coverage (3 tests) ⚠️
- Mobile Experience: 60% coverage (5 tests)
- API Endpoints: 75% coverage (12 tests)

**Coverage Gaps Identified:**

1. **Admin Functions** - Low coverage area
   - Missing: Bulk user management tests
   - Missing: Advanced reporting tests
   - Missing: System configuration tests

2. **Edge Cases** - Across all areas
   - Error handling scenarios: 40% covered
   - Network failure recovery: 30% covered
   - Data validation edge cases: 55% covered

3. **Performance Testing**
   - Load testing: Limited coverage
   - Stress testing: No coverage
   - Concurrent user scenarios: Minimal

**Recommendations for New Feature:**

1. **Plan Tests Early:** Design tests alongside feature
2. **Focus on Gaps:** Improve admin and edge case coverage
3. **Add Performance Tests:** Include load/stress scenarios
4. **Consider Integration:** How feature affects existing flows

**Test Strategy Template:**
```
New Feature: [Your Feature Name]
- Unit Tests: [Component level]
- Integration Tests: [Feature interaction]  
- E2E Tests: [Full user journey]
- Performance Tests: [Load/response time]
- Edge Cases: [Error scenarios]
```

Would you like me to create a specific test plan for your new feature?
```

This comprehensive guide shows how the TestZeus MCP Server integrates seamlessly with both Claude Desktop and Cursor IDE to provide intelligent testing assistance that feels natural and conversational. 