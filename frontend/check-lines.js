const fs = require('fs');
const content = fs.readFileSync('app/(auth)/login/page.tsx', 'utf8');
const lines = content.split('\n');
for (let i = 75; i <= 110; i++) {
  const line = lines[i];
  console.log((i+1).toString().padStart(3) + ': ' + JSON.stringify(line));
}