import { google } from 'googleapis';
import { getAuthenticatedClient } from './googleAuth';

export interface CalendarEvent {
  id: string;
  title: string;
  start: string;
  end: string;
  location?: string;
  description?: string;
  attendees?: string[];
}

export async function getEvents(options: {
  daysAhead?: number;
  daysBack?: number;
  maxResults?: number;
} = {}): Promise<CalendarEvent[]> {
  const auth = getAuthenticatedClient();
  const calendar = google.calendar({ version: 'v3', auth });

  const now = new Date();

  const timeMin = new Date(now);
  timeMin.setDate(timeMin.getDate() - (options.daysBack ?? 0));
  timeMin.setHours(0, 0, 0, 0);

  const timeMax = new Date(now);
  timeMax.setDate(timeMax.getDate() + (options.daysAhead ?? 1));
  timeMax.setHours(23, 59, 59, 999);

  const { data } = await calendar.events.list({
    calendarId: 'primary',
    timeMin: timeMin.toISOString(),
    timeMax: timeMax.toISOString(),
    singleEvents: true,
    orderBy: 'startTime',
    maxResults: options.maxResults ?? 50,
  });

  return (data.items ?? []).map((e) => ({
    id: e.id ?? '',
    title: e.summary ?? '(No title)',
    start: e.start?.dateTime ?? e.start?.date ?? '',
    end: e.end?.dateTime ?? e.end?.date ?? '',
    location: e.location ?? undefined,
    description: e.description ?? undefined,
    attendees: e.attendees?.map((a) => a.email ?? '').filter(Boolean),
  }));
}
