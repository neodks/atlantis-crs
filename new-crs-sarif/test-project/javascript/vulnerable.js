const express = require('express');
const { exec } = require('child_process');

const app = express();

app.get('/run', (req, res) => {
  const cmd = req.query.cmd;
  exec(cmd, (err, stdout, stderr) => {
    if (err) {
      console.error(err);
      return res.status(500).send('Error');
    }
    res.send(stdout);
  });
});

app.listen(3000, () => {
  console.log('App listening on port 3000');
});
