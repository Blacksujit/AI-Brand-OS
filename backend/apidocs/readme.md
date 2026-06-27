# Content API Endpoints

## POST /content/ideas

Generate content ideas based on user context and preferences.

### Request Body

```json
{
  "topic": "optional topic to guide idea generation",
  "platform": "platform for ideas (linkedin, twitter, etc.)",
  "count": 5,
  "expertise_areas": ["data-science", "productivity", "leadership"]
}
```

### Response

Returns a list of AI-generated content ideas with title, description, relevance_score, and platform.

```json
[
  {
    "id": "uuid",
    "title": "How to build a data-driven culture in your team",
    "description": "A practical guide to implementing data-driven decision making processes",
    "relevance_score": 0.87,
    "platform": "linkedin"
  },
  {
    "id": "uuid", 
    "title": "5 habits of highly effective remote teams",
    "description": "Key practices for maintaining productivity and engagement in distributed teams",
    "relevance_score": 0.76,
    "platform": "linkedin"
  }
]
```

### HTTP Status Codes

- **200**: Success with list of generated ideas
- **400**: Invalid request (validation errors)

### Notes

The ideas are generated based on:
- User's recent GitHub activity
- User's knowledge base entries and tags
- Current trending topics
- User's specific expertise areas

The relevance_score is a value between 0.0 and 1.0, where higher scores indicate better alignment with the user's profile and context.

### Security

Requires authentication via JWT bearer token. User must be onboarded.

### Rate Limiting

Standard API rate limits apply. Excessive calls may trigger rate limiting responses.

### Client Example (JavaScript)

```javascript
fetch('/api/content/ideas', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN_HERE'
  },
  body: JSON.stringify({
    topic: 'team productivity',
    platform: 'linkedin',
    count: 10,
    expertise_areas: ['leadership', 'motivation']
  })
})
.then(response => response.json())
.then(ideas => {
  console.log(`Generated ${ideas.length} ideas`);
  ideas.forEach(idea => {
    console.log(`${idea.title} (${idea.relevance_score}): ${idea.description}`);
  });
});
```