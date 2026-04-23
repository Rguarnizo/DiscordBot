// start.js

import { spawn } from "child_process";

// Lanzar script Node
spawn("node", ["/home/node/app.js"], {
  stdio: "inherit",
});

// Lanzar n8n
spawn("n8n", [], {
  stdio: "inherit",
});