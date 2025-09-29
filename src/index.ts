import express from 'express';
import { json } from 'body-parser';
import healthRouter from './routes/health.js';
import logger from './utils/logger.js';

const PORT = process.env.PORT || 3000;
const app = express();
app.use(json());

app.use('/health', healthRouter);

app.get('/', (req, res) => {
  res.json({ status: 'ok', message: 'Welcome to bookeditor-starter' });
});

app.listen(PORT, () => {
  logger.info(`Server running on http://localhost:${PORT}`);
});
