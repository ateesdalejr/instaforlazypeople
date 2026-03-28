import 'dotenv/config';
import { getEmails, getEmailBody } from './gmail';
import { getEvents } from './calendar';

async function test() {
  console.log('\n--- Testing Gmail (summaries) ---');
  const emails = await getEmails({ daysBack: 3, maxResults: 3 });
  if (emails.length === 0) {
    console.log('No emails found in last 3 days.');
  } else {
    for (let i = 0; i < emails.length; i++) {
      const full = await getEmailBody(emails[i].id);
      console.log(`\n--- Email ${i + 1} of ${emails.length} ---`);
      console.log(`Subject: ${full.subject}`);
      console.log(`From:    ${full.from}`);
      console.log(`Date:    ${full.date}`);
      console.log(`\n${full.body}`);
    }
  }

  console.log('\n--- Testing Calendar ---');
  const events = await getEvents({ daysBack: 1, daysAhead: 3 });
  if (events.length === 0) {
    console.log('No calendar events found.');
  } else {
    events.forEach(e => console.log(`  [${e.start}] ${e.title}`));
  }
}

test().catch(console.error);
