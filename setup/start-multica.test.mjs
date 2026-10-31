import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createEnv, publishedUrl } from './start-multica.mjs';

test('generates unique secrets and keeps database credentials consistent', () => {
  const template = readFileSync(new URL('../../multica/.env.example', import.meta.url), 'utf8');
  const result = createEnv(template);
  const value = (key) => new RegExp(`^${key}=(.*)$`, 'm').exec(result)?.[1];
  assert.match(value('JWT_SECRET'), /^[a-f0-9]{64}$/);
  assert.match(value('POSTGRES_PASSWORD'), /^[a-f0-9]{48}$/);
  assert.ok(value('DATABASE_URL').includes(`:${value('POSTGRES_PASSWORD')}@`));
  assert.equal(Buffer.from(value('MULTICA_VCS_SECRET_KEY'), 'base64').length, 32);
  assert.equal(Buffer.from(value('MULTICA_SLACK_SECRET_KEY'), 'base64').length, 32);
  assert.notEqual(result, createEnv(template));
});

test('fails on an incompatible environment template', () => {
  assert.throws(() => createEnv('JWT_SECRET=old'), /Missing/);
});

test('uses the actual published localhost port', () => {
  assert.equal(publishedUrl('127.0.0.1:4300\r\n'), 'http://127.0.0.1:4300');
  assert.throws(() => publishedUrl('0.0.0.0:3000'), /local-only/);
  assert.throws(() => publishedUrl(''), /local-only/);
});
