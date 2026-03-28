import 'dotenv/config';
import * as readline from 'readline';
import { getEmails, getEmailBody } from './gmail';
import { getEvents } from './calendar';

const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

function ask(question: string): Promise<string> {
  return new Promise((resolve) => rl.question(question, (a) => resolve(a.trim())));
}

function printDivider(title: string) {
  console.log('\n' + '═'.repeat(50));
  console.log(`  ${title}`);
  console.log('═'.repeat(50));
}

async function pullGmail(daysBack: number) {
  printDivider('GMAIL');
  console.log(`Fetching emails from last ${daysBack} day(s)...\n`);

  const emails = await getEmails({ daysBack, maxResults: 20 });
  if (emails.length === 0) { console.log('No emails found.'); return; }

  emails.forEach((e, i) => {
    console.log(`[${i + 1}] ${e.date}`);
    console.log(`    From:    ${e.from}`);
    console.log(`    Subject: ${e.subject}`);
    console.log(`    Preview: ${e.snippet.slice(0, 100)}`);
    console.log();
  });
  console.log(`Total: ${emails.length} email(s)`);

  const pick = await ask('\nEnter email number to read full body (or Enter to skip): ');
  if (pick) {
    const idx = parseInt(pick, 10) - 1;
    if (emails[idx]) {
      const full = await getEmailBody(emails[idx].id);
      printDivider(`FULL EMAIL: ${full.subject}`);
      console.log(`From: ${full.from}`);
      console.log(`Date: ${full.date}\n`);
      console.log(full.body);
    }
  }
}

async function pullCalendar(daysBack: number, daysAhead: number) {
  printDivider('GOOGLE CALENDAR');
  console.log(`Fetching events (${daysBack} days back, ${daysAhead} days ahead)...\n`);

  const events = await getEvents({ daysBack, daysAhead, maxResults: 50 });
  if (events.length === 0) { console.log('No events found.'); return; }

  events.forEach((e, i) => {
    console.log(`[${i + 1}] ${e.title}`);
    console.log(`    Start:    ${e.start}`);
    console.log(`    End:      ${e.end}`);
    if (e.location)          console.log(`    Location: ${e.location}`);
    if (e.attendees?.length) console.log(`    Attendees: ${e.attendees.join(', ')}`);
    console.log();
  });
  console.log(`Total: ${events.length} event(s)`);
}

async function main() {
  console.log('\n╔══════════════════════════════════╗');
  console.log('║     Daily Events Data Puller     ║');
  console.log('╚══════════════════════════════════╝');

  console.log('\nWhat do you want to pull?');
  console.log('  1. Gmail only');
  console.log('  2. Calendar only');
  console.log('  3. Both');

  const choice = await ask('\nChoice (1-3): ');
  const daysBack = parseInt(await ask('How many days back? (default: 1): ') || '1', 10);

  try {
    if (choice === '1' || choice === '3') await pullGmail(daysBack);
    if (choice === '2' || choice === '3') await pullCalendar(daysBack, 7);
  } catch (err: any) {
    console.error('\n✗ Error:', err.message);
    if (err.message?.includes('tokens')) {
      console.log('  Run: npm run auth:google');
    }
  }

  rl.close();
}

main();
