import { NextResponse } from 'next/server'
import { readdir, readFile } from 'fs/promises'
import path from 'path'
import OpenAI from 'openai'

const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY })

const UPLOAD_DIR = path.join(process.cwd(), 'uploaded_repos')

async function readSessionFiles(sessionId) {
  const sessionDir = path.join(UPLOAD_DIR, sessionId)
  const files = []

  async function walkDir(dir, baseDir) {
    const entries = await readdir(dir, { withFileTypes: true })
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name)
      const relativePath = path.relative(baseDir, fullPath)
      if (entry.isDirectory()) {
        await walkDir(fullPath, baseDir)
      } else {
        try {
          const content = await readFile(fullPath, 'utf-8')
          files.push({ name: relativePath, content })
        } catch {
          // Skip binary files
        }
      }
    }
  }

  await walkDir(sessionDir, sessionDir)
  return files
}

function buildCodebaseContext(files) {
  return files
    .map(f => `=== FILE: ${f.name} ===\n${f.content}`)
    .join('\n\n')
}

export async function POST(request) {
  try {
    const { question, sessionId } = await request.json()

    if (!question) {
      return NextResponse.json({ error: 'No question provided' }, { status: 400 })
    }

    if (!sessionId) {
      return NextResponse.json({ error: 'No upload session found. Please upload a repo first.' }, { status: 400 })
    }

    if (!process.env.OPENAI_API_KEY) {
      return NextResponse.json({ error: 'OPENAI_API_KEY is not set in .env.local' }, { status: 500 })
    }

    const files = await readSessionFiles(sessionId)

    if (files.length === 0) {
      return NextResponse.json({ error: 'No readable files found in the uploaded session.' }, { status: 400 })
    }

    const codebaseContext = buildCodebaseContext(files)
    const fileList = files.map(f => f.name)

    const completion = await client.chat.completions.create({
      model: 'gpt-4o-mini',
      max_tokens: 4096,
      messages: [
        {
          role: 'system',
          content: 'You are an expert code analyst. Respond only with raw JSON, no markdown, no backticks.',
        },
        {
          role: 'user',
          content: `A user has uploaded a codebase and wants to understand it.

Here are all the files in the codebase:
<codebase>
${codebaseContext}
</codebase>

The user's question is: "${question}"

Respond with a JSON object in this exact format:
{
  "confidence": 0.85,
  "confidenceLabel": "High",
  "claims": [
    {
      "title": "Short title for this finding",
      "body": "Detailed explanation of this aspect of the codebase",
      "relevantFiles": ["filename.py", "other.py"]
    }
  ],
  "evidence": [
    {
      "filename": "path/to/file.py",
      "startLine": 1,
      "endLine": 30,
      "relevance": 0.92,
      "snippet": "the actual code snippet from this file, max 5 lines"
    }
  ]
}

Guidelines:
- confidence should be 0.0 to 1.0 based on how well the files answer the question
- confidenceLabel should be "High", "Medium", or "Low"
- provide 2-5 claims that directly answer the question
- provide 3-7 evidence items showing the most relevant code snippets
- relevantFiles in claims should reference actual filenames from the codebase
- relevance in evidence should be 0.0 to 1.0
- keep snippets short (3-6 lines) and directly relevant
- only reference files that actually exist in the provided codebase`,
        },
      ],
    })

    let result
    try {
      const text = completion.choices[0].message.content.trim()
      const clean = text.replace(/^```json?\s*/i, '').replace(/```\s*$/i, '').trim()
      result = JSON.parse(clean)
    } catch {
      return NextResponse.json(
        { error: 'Failed to parse response. Try again.' },
        { status: 500 }
      )
    }

    return NextResponse.json({
      success: true,
      question,
      confidence: result.confidence ?? 0.5,
      confidenceLabel: result.confidenceLabel ?? 'Medium',
      claims: result.claims ?? [],
      evidence: result.evidence ?? [],
      totalFiles: files.length,
      fileList,
    })

  } catch (error) {
    console.error('Ask error:', error)
    return NextResponse.json(
      { error: error.message || 'Something went wrong' },
      { status: 500 }
    )
  }
}
