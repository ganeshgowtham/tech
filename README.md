Here are some example functional and non-functional requirements for a commercial payment solution:

### Functional Requirements

1. **User Authentication**: 
   - The system must allow users to register and log in using a username and password.
   - The system should support multi-factor authentication (MFA) for additional security.

2. **Transaction Processing**:
   - The system must support various payment methods (credit cards, debit cards, bank transfers, digital wallets).
   - The system should process payments within a specified time frame (e.g., within 5 seconds).

3. **Invoice Management**:
   - The system must allow businesses to generate, send, and manage invoices.
   - The system should enable customers to view and pay invoices online.

4. **Currency Handling**:
   - The system must support transactions in multiple currencies.
   - The system should automatically convert currencies based on current exchange rates.

5. **Refunds and Disputes**:
   - The system must allow users to request refunds and manage disputes.
   - The system should track the status of refunds and disputes.

6. **Reporting and Analytics**:
   - The system must provide businesses with detailed transaction reports.
   - The system should offer analytics tools to analyze payment trends and customer behavior.

### Non-Functional Requirements

1. **Performance**:
   - The system should handle up to 10,000 transactions per minute with a response time of less than 2 seconds.
   - The system should maintain performance levels under peak load conditions.

2. **Scalability**:
   - The system must be able to scale horizontally to accommodate increasing numbers of users and transactions.
   - The system should support auto-scaling based on demand.

3. **Security**:
   - The system must encrypt all sensitive data in transit and at rest.
   - The system should comply with PCI-DSS standards for handling payment card information.

4. **Usability**:
   - The system should have an intuitive and user-friendly interface.
   - The system must provide clear and concise error messages.

5. **Reliability**:
   - The system should have an uptime of 99.99%.
   - The system must support automatic failover and data recovery in case of failures.

6. **Maintainability**:
   - The system should be easy to update with minimal downtime.
   - The system must provide comprehensive logging and monitoring to facilitate troubleshooting.

7. **Compatibility**:
   - The system must be compatible with major web browsers and mobile operating systems.
   - The system should integrate with commonly used accounting and ERP systems.

8. **Compliance**:
   - The system must adhere to GDPR for handling customer data.
   - The system should comply with local financial regulations in all operating regions.