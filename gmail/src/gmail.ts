import { google } from 'googleapis';
import { getAuthenticatedClient } from './googleAuth';

export interface EmailFull {
  id: string;
  date: string;
  from: string;
  subject: string;
  snippet: string;
  body: string;
}

function getHeader(headers: any[], name: string): string {
  return headers.find((h: any) => h.name.toLowerCase() === name.toLowerCase())?.value ?? '';
}

function findPart(payload: any, mimeType: string): string | null {
  if (!payload) return null;
  if (payload.mimeType === mimeType && payload.body?.data) {
    return Buffer.from(payload.body.data, 'base64').toString('utf-8');
  }
  for (const part of payload.parts ?? []) {
    const found = findPart(part, mimeType);
    if (found) return found;
  }
  return null;
}

function extractBody(payload: any): string {
  let body = findPart(payload, 'text/plain');
  if (!body) {
    const html = findPart(payload, 'text/html');
    if (html) body = html.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
  }
  return body ?? '(no body)';
}

export async function getEmailsFull(options: {
  maxResults?: number;
  daysBack?: number;
} = {}): Promise<EmailFull[]> {
  const auth = getAuthenticatedClient();
  const gmail = google.gmail({ version: 'v1', auth });

  let q = '';
  if (options.daysBack) {
    const d = new Date();
    d.setDate(d.getDate() - options.daysBack);
    q = `after:${d.toISOString().split('T')[0].replace(/-/g, '/')}`;
  }

  const listRes = await gmail.users.messages.list({
    userId: 'me',
    q: q || undefined,
    maxResults: options.maxResults ?? 20,
  });

  const messages = listRes.data.messages ?? [];
  if (messages.length === 0) return [];

  // Fetch all full messages in parallel
  const results = await Promise.all(
    messages.map(async ({ id }) => {
      const { data } = await gmail.users.messages.get({
        userId: 'me',
        id: id!,
        format: 'full',
      });
      const headers = data.payload?.headers ?? [];
      return {
        id: id!,
        date: getHeader(headers, 'Date'),
        from: getHeader(headers, 'From'),
        subject: getHeader(headers, 'Subject'),
        snippet: data.snippet ?? '',
        body: extractBody(data.payload),
      };
    })
  );

  return results;
}

// Still exported for use in test.ts
export async function getEmailBody(id: string): Promise<EmailFull> {
  const auth = getAuthenticatedClient();
  const gmail = google.gmail({ version: 'v1', auth });

  const { data } = await gmail.users.messages.get({
    userId: 'me',
    id,
    format: 'full',
  });

  const headers = data.payload?.headers ?? [];
  return {
    id,
    date: getHeader(headers, 'Date'),
    from: getHeader(headers, 'From'),
    subject: getHeader(headers, 'Subject'),
    snippet: data.snippet ?? '',
    body: extractBody(data.payload),
  };
}

// Kept for test.ts compatibility
export async function getEmails(options: {
  maxResults?: number;
  daysBack?: number;
} = {}): Promise<EmailFull[]> {
  return getEmailsFull(options);
}
