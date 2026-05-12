export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { topic } = req.body || {};
  if (!topic) {
    return res.status(400).json({ error: 'topic is required' });
  }

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ error: 'ANTHROPIC_API_KEY not set in Vercel environment variables' });
  }

  const system = `You are a content writer for Conrad Palmer, a mortgage broker at Loan Market Gold Coast, Australia.
Generate Instagram carousel slides as JSON for the topic provided.

VOICE RULES:
- British English (not American)
- Short, punchy sentences. Plain language, no jargon.
- Warm but direct. Knowledgeable without being showy.
- First home buyers, investors, and refinancers are the audience.
- Never use "delve", "navigate", "leverage", "bolster", "pivotal", "transformative", "game-changing", or similar AI buzzwords.

SLIDE RULES:
- Always start with a "hook" slide and end with a "cta" slide.
- 6–9 slides total.
- Mix types for variety: hook, content, data_stat, comparison, cta.
- date_tag on hook slide: use today's date formatted like "MAY 12, 2026".
- accent_word on content slides: one word only, must appear in the headline text.

FIXED CTA DEFAULTS (use exactly):
- name: "Conrad Palmer"
- title: "Loan Market | Gold Coast"
- social_proof: "★★★★★  150+ Google Reviews"

RETURN: Only valid raw JSON — no markdown fences, no explanation, just the JSON object.

Schema:
{
  "output_folder": "output_slides",
  "slides": [
    // hook:       { "type": "hook",       "date_tag": "...", "headline": "..." }
    // content:    { "type": "content",    "headline": "...", "accent_word": "...", "body": "..." }
    // data_stat:  { "type": "data_stat",  "label": "...", "big_number": "...", "supporting_text": "..." }
    // comparison: { "type": "comparison", "label": "...", "strikethrough_number": "...", "corrected_number": "...", "supporting_text": "..." }
    // cta:        { "type": "cta",        "cta_prompt": "...", "keyword": "...", "supporting_text": "...", "name": "...", "title": "...", "social_proof": "..." }
  ]
}`;

  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: 'claude-opus-4-6',
        max_tokens: 2048,
        system,
        messages: [{ role: 'user', content: `Topic: ${topic}` }],
      }),
    });

    if (!response.ok) {
      const err = await response.text();
      return res.status(response.status).json({ error: err });
    }

    const data = await response.json();
    const raw  = (data.content?.[0]?.text || '').trim();

    let parsed;
    try {
      parsed = JSON.parse(raw);
    } catch {
      // Strip any accidental markdown fences and retry
      const match = raw.match(/\{[\s\S]*\}/);
      if (!match) throw new Error('Claude did not return valid JSON');
      parsed = JSON.parse(match[0]);
    }

    return res.status(200).json(parsed);

  } catch (err) {
    console.error('[draft]', err);
    return res.status(500).json({ error: err.message });
  }
}
