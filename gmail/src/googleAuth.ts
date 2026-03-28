import { google } from 'googleapis';
import * as fs from 'fs';
import * as path from 'path';
import * as readline from 'readline';

const TOKENS_PATH = path.join(__dirname, '..', 'google_tokens.json');

const SCOPES = [
  'https://www.googleapis.com/auth/gmail.readonly',
  'https://www.googleapis.com/auth/calendar.readonly',
];

export function createOAuthClient() {
  return new google.auth.OAuth2(
    process.env.GOOGLE_CLIENT_ID!,
    process.env.GOOGLE_CLIENT_SECRET!,
    process.env.GOOGLE_REDIRECT_URI!
  );
}

export function getAuthUrl(): string {
  const client = createOAuthClient();
  return client.generateAuthUrl({
    access_type: 'offline',
    scope: SCOPES,
    prompt: 'consent',
  });
}

export async function exchangeCodeForTokens(code: string): Promise<void> {
  const client = createOAuthClient();
  const { tokens } = await client.getToken(code);
  fs.writeFileSync(TOKENS_PATH, JSON.stringify(tokens, null, 2));
  console.log('✓ Google tokens saved to google_tokens.json');
}

export function getAuthenticatedClient() {
  if (!fs.existsSync(TOKENS_PATH)) {
    throw new Error(
      'No Google tokens found. Run "npm run auth:google" first to authenticate.'
    );
  }
  const tokens = JSON.parse(fs.readFileSync(TOKENS_PATH, 'utf-8'));
  const client = createOAuthClient();
  client.setCredentials(tokens);

  // Auto-refresh token when expired
  client.on('tokens', (newTokens) => {
    const existing = JSON.parse(fs.readFileSync(TOKENS_PATH, 'utf-8'));
    fs.writeFileSync(TOKENS_PATH, JSON.stringify({ ...existing, ...newTokens }, null, 2));
  });

  return client;
}

// Run directly: ts-node src/googleAuth.ts
if (require.main === module) {
  require('dotenv/config');
  runAuthFlow().catch(console.error);
}

export async function runAuthFlow(): Promise<void> {
  const url = getAuthUrl();
  console.log('\n--- Google OAuth Setup ---');
  console.log('1. Open this URL in your browser:\n');
  console.log(url);
  console.log('\n2. Log in and grant access.');
  console.log('3. You will be redirected to localhost (it will fail to load — that is normal).');
  console.log('4. Copy the "code" parameter from the URL.\n');

  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const code = await new Promise<string>((resolve) => {
    rl.question('Paste the code here: ', (answer) => {
      rl.close();
      resolve(answer.trim());
    });
  });

  await exchangeCodeForTokens(code);
}
