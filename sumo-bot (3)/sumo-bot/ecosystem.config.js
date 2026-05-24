module.exports = {
  apps: [{
    name: "sumo-bot",
    script: "main.py",
    interpreter: "python",
    restart_delay: 5000,
    max_restarts: 10,
    env: { NODE_ENV: "production" }
  }]
};
