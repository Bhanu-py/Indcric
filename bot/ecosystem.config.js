// PM2 process config for the IndCric group bot (Phase 3 hosting).
//   pm2 start ecosystem.config.js   # launch under supervision
//   pm2 save && pm2 startup          # survive VM reboots
// See DEPLOY.md.
module.exports = {
  apps: [{
    name: 'indcric-bot',
    script: 'bot.js',
    cwd: __dirname,
    autorestart: true,        // restart on crash / transient disconnect
    max_restarts: 10,
    restart_delay: 5000,
    // ~9s graceful shutdown so Chromium flushes the WA session (IndexedDB) before exit.
    kill_timeout: 10000,
    max_memory_restart: '800M',
    env: { NODE_ENV: 'production' },
  }],
};
