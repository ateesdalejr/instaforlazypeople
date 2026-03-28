import 'dotenv/config';
import express from 'express';
import { getEmailsFull } from './gmail';
import { getEvents } from './calendar';

const app = express();
const PORT = process.env.PORT ?? 3000;

app.get('/health', (_req, res) => {
  res.json({ status: 'ok' });
});

app.get('/data', async (req, res) => {
  const days = parseInt((req.query.days as string) ?? '1', 10);
  const maxResults = parseInt((req.query.maxResults as string) ?? '20', 10);

  const [emails, events] = await Promise.all([
    getEmailsFull({ daysBack: days, maxResults }),
    getEvents({ daysBack: days, daysAhead: 0, maxResults }),
  ]);

  res.json({ emails, events });
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
  console.log(`Endpoint: GET /data?days=7&maxResults=20`);
});
