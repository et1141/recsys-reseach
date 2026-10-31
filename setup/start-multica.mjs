import { randomBytes } from 'node:crypto';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve, join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../../multica');
const files = ['-f', 'docker-compose.selfhost.yml', '-f', 'docker-compose.selfhost.build.yml'];

export function createEnv(template) {
  const password = randomBytes(24).toString('hex');
  const values = {
    JWT_SECRET: randomBytes(32).toString('hex'),
    POSTGRES_PASSWORD: password,
    MULTICA_VCS_SECRET_KEY: randomBytes(32).toString('base64'),
    MULTICA_SLACK_SECRET_KEY: randomBytes(32).toString('base64'),
  };
  let content = template.replace(/\r\n/g, '\n');
  for (const [key, value] of Object.entries(values)) {
    const pattern = new RegExp(`^${key}=.*$`, 'm');
    if (!pattern.test(content)) throw new Error(`Missing ${key} in upstream .env.example`);
    content = content.replace(pattern, `${key}=${value}`);
  }
  return content.replace(/^(DATABASE_URL=postgres:\/\/[^:]+:)[^@]*/m, `$1${password}`);
}

export function publishedUrl(output) {
  const binding = output.trim().split(/\r?\n/)[0];
  const match = /^127\.0\.0\.1:(\d+)$/.exec(binding);
  if (!match) throw new Error(`Expected a local-only published port; received ${binding}`);
  return `http://127.0.0.1:${match[1]}`;
}

function execute(binary, args, { capture = false, required = true, timeout = 0, env } = {}) {
  const result = spawnSync(binary, args, {
    cwd: repo, encoding: 'utf8', windowsHide: true,
    stdio: capture ? 'pipe' : 'inherit', timeout, env: env ?? process.env,
  });
  if (required && (result.error || result.status !== 0)) {
    throw new Error(result.error?.message ?? `${binary} ${args.slice(0, 2).join(' ')} failed (${result.status}).`);
  }
  return result;
}

const sleep = (ms) => new Promise((done) => setTimeout(done, ms));

async function waitFor(check, seconds, message) {
  const deadline = Date.now() + seconds * 1000;
  do {
    if (await check()) return;
    await sleep(2000);
  } while (Date.now() < deadline);
  throw new Error(message);
}

async function main() {
  const options = process.argv.slice(2);
  if (options.some((arg) => !['--stop', '--logs', '--no-open', '--help'].includes(arg)) ||
      (options.includes('--stop') && options.includes('--logs'))) {
    throw new Error('Usage: Start-Multica.cmd [--no-open | --stop | --logs | --help]');
  }
  if (options.includes('--help')) {
    console.log('Start-Multica.cmd: build/start Docker services and open Multica.\n' +
      '--no-open: skip browser; --stop: stop services, retain data; --logs: follow service logs.');
    return;
  }
  if (!existsSync(join(repo, 'docker-compose.selfhost.yml'))) {
    throw new Error(`Multica checkout not found at ${repo}`);
  }
  let docker = 'docker';
  if (spawnSync(docker, ['--version'], { windowsHide: true }).status !== 0) {
    docker = join(process.env.ProgramFiles ?? 'C:/Program Files', 'Docker/Docker/resources/bin/docker.exe');
    if (!existsSync(docker)) {
      throw new Error('Docker Desktop is not installed or accessible. Install Docker Desktop, enable Linux containers, then run Start-Multica.cmd again.');
    }
  }
  const engineReady = () => execute(docker, ['info'], { capture: true, required: false, timeout: 10000 }).status === 0;
  if (!engineReady()) {
    const desktop = join(process.env.ProgramFiles ?? 'C:/Program Files', 'Docker/Docker/Docker Desktop.exe');
    if (process.platform === 'win32' && existsSync(desktop)) {
      console.log('Starting Docker Desktop...');
      execute('powershell.exe', ['-NoProfile', '-Command',
        "Start-Process -FilePath $env:MULTICA_DOCKER_DESKTOP -WindowStyle Hidden"],
      { env: { ...process.env, MULTICA_DOCKER_DESKTOP: desktop } });
    }
    await waitFor(engineReady, 180, 'Docker engine did not become ready. Open Docker Desktop and check its status.');
  }
  execute(docker, ['compose', 'version']);
  const compose = (...args) => execute(docker, ['compose', ...files, ...args]);
  if (options.includes('--stop')) {
    compose('stop');
    console.log('Multica stopped. Database and uploads retained.');
    return;
  }
  if (options.includes('--logs')) {
    compose('logs', '--follow', '--tail', '100');
    return;
  }
  const envPath = join(repo, '.env');
  if (!existsSync(envPath)) {
    writeFileSync(envPath, createEnv(readFileSync(join(repo, '.env.example'), 'utf8')),
      { encoding: 'utf8', flag: 'wx', mode: 0o600 });
    console.log('Created local configuration with fresh secrets.');
  }
  console.log('Building and starting Multica with Docker (first build can take several minutes)...');
  compose('up', '--detach', '--build');
  const port = (service, internal) => publishedUrl(execute(docker,
    ['compose', ...files, 'port', service, internal], { capture: true }).stdout);
  const api = port('backend', '8080');
  const web = port('frontend', '3000');
  console.log('Waiting for database migrations, API and web app...');
  await waitFor(async () => {
    try {
      const ready = await fetch(`${api}/readyz`, { signal: AbortSignal.timeout(5000) });
      const health = await ready.json();
      if (!ready.ok || health.status !== 'ok' || health.checks?.db !== 'ok' ||
          health.checks?.migrations !== 'ok') return false;
      const frontend = await fetch(web, { signal: AbortSignal.timeout(5000) });
      return frontend.ok;
    } catch { return false; }
  }, 180, 'Services did not become ready. Run Start-Multica.cmd --logs to inspect the failure.');
  console.log(`Multica ready: ${web}\nStop later with: Start-Multica.cmd --stop`);
  if (!options.includes('--no-open') && process.platform === 'win32') {
    execute('powershell.exe', ['-NoProfile', '-Command', 'Start-Process $env:MULTICA_OPEN_URL'],
      { env: { ...process.env, MULTICA_OPEN_URL: web } });
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.error(`\nMultica did not start: ${error.message}`);
    process.exitCode = 1;
  });
}
