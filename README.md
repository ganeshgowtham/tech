I am John Doe from the Payment Operations team. Today, I will show you how to repair payments stuck in the SWIFT truncation exception queue.


First, I log in to the Global Money Transfer System (GMTS) web application.


After logging in, I navigate to the 'Exception Processing' under the 'Payment Menu' to see the list of repair queues. I select the "SWIFT Truncation Queue" by setting its priority to 1, then click the detail button.


On the details page, I see the list of payment transactions. I navigate to the last page to view the most recent transaction. Then, I click on the last transaction to view all its details.


I scroll to the bottom of the page to find the transaction that needs repair and note the sender reference ID.


Next, I search for this Sender Reference ID in the Message Gateway application, then return to GMTS.


I enter the USN obtained from the Message Gateway into the transaction detail page.


After entering the USN, I click Validate to check for any errors.


If validation passes, the Submit button appears. I click Submit to complete the repair.


Finally, I return to the transactions list and click the Summary button to go back to the home page.