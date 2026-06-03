// Minimal responder: reads comment, calls an LLM, posts a reply.
// Node 18+ has fetch built-in.
import fs from 'fs';

const eventPath = process.env.GITHUB_EVENT_PATH;
if (!eventPath) {
  console.error('GITHUB_EVENT_PATH not set'); process.exit(1);
}
const event = JSON.parse(fs.readFileSync(eventPath, 'utf8'));
const comment = event.comment?.body || '';
const author = event.comment?.user?.login || '';
const repo = process.env.GITHUB_REPOSITORY; // owner/repo
const [owner, repoName] = repo.split('/');

if (!comment.includes('@copilot')) {
  console.log('No @copilot mention; exiting.'); process.exit(0);
}
// Avoid responding to bot comments or ourselves
if (author === 'github-actions[bot]' || author === 'copilot' || author === 'Copilot') {
  console.log('Comment authored by bot; exiting.'); process.exit(0);
}

// Build prompt. Adjust for more context if desired.
const prompt = `A reviewer on GitHub wrote:\n\n${comment}\n\nPlease write a polite, concise reply addressing the points raised and suggest next steps.`;

async function callLLM(promptText) {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) throw new Error('OPENAI_API_KEY missing');
  const res = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      model: 'gpt-4o-mini', // replace with your model if needed
      messages: [{ role: 'user', content: promptText }],
      max_tokens: 500
    })
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error('LLM error: ' + txt);
  }
  const data = await res.json();
  return data.choices?.[0]?.message?.content?.trim() ?? '';
}

async function postReply(body) {
  // Prefer a BOT_TOKEN secret (machine user) for clear provenance; fallback to GITHUB_TOKEN
  const token = process.env.BOT_TOKEN || process.env.GITHUB_TOKEN;
  if (!token) throw new Error('No token available to post reply');
  const issueNumber = event.issue?.number || event.pull_request?.number;
  if (!issueNumber) throw new Error('No issue/PR number in event payload');

  const url = `https://api.github.com/repos/${owner}/${repoName}/issues/${issueNumber}/comments`;
  const resp = await fetch(url, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
      Accept: 'application/vnd.github.v3+json'
    },
    body: JSON.stringify({ body })
  });
  if (!resp.ok) {
    const txt = await resp.text();
    throw new Error('GitHub post failed: ' + txt);
  }
  console.log('Posted reply.');
}

(async () => {
  try {
    const reply = await callLLM(prompt);
    // include a clear provenance header as requested
    const final = `Copilot Response:\n\n${reply}`;
    await postReply(final);
  } catch (e) {
    console.error('Error:', e);
    process.exit(1);
  }
})();
