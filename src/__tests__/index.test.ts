import request from 'supertest';
import express from 'express';
import healthRouter from '../routes/health.js';

const app = express();
app.use('/health', healthRouter);

describe('GET /health', () => {
  test('returns 200', async () => {
    const res = await request(app).get('/health');
    expect(res.status).toBe(200);
    expect(res.body).toEqual({ status: 'ok' });
  });
});
