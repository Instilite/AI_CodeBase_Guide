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

export async function POST(request) {
  try {
    const { sessionId } = await request.json()

    if (!sessionId) {
      return NextResponse.json({ error: 'No upload session found. Please upload a repo first.' }, { status: 400 })
    }

    const files = await readSessionFiles(sessionId)

    if (files.length === 0) {
      return NextResponse.json({ error: 'No readable files found.' }, { status: 400 })
    }

    const fileList = files.map(f => `${f.name} (${f.content.split('\n').length} lines)`).join('\n')
    const fileContents = files.map(f => `=== FILE: ${f.name} ===\n${f.content}`).join('\n\n')

    const completion = await client.chat.completions.create({
      model: 'gpt-4o-mini',
      max_tokens: 2048,
      messages: [
        {
          role: 'system',
          content: 'You are an expert code analyst. Respond only with raw JSON, no markdown, no backticks.',
        },
        {
          role: 'user',
          content: `Analyze this codebase and rank the files by their impact and importance to the overall project.

Files in the codebase:
${fileList}

File contents:
${fileContents}

Respond with a JSON object in this exact format:
{
  "files": [
    {
      "filename": "path/to/file.py",
      "impact": 0.95,
      "impactLabel": "High",
      "summary": "One sentence describing the core functionality of this file"
    }
  ]
}

Guidelines:
- impact should be 0.0 to 1.0
- impactLabel should be "High", "Medium", or "Low"
- High = core logic, entry points, main modules that everything depends on
- Medium = important but not central, utility files, helpers
- Low = config files, minor utilities, standalone scripts
- summary must be a single concise sentence describing what this file does
- rank files from highest to lowest impact
- include all files`,
        },
      ],
    })

    let result
    try {
      const text = completion.choices[0].message.content.trim()
      const clean = text.replace(/^```json?\s*/i, '').replace(/```\s*$/i, '').trim()
      result = JSON.parse(clean)
    } catch {
      return NextResponse.json({ error: 'Failed to parse response. Try again.' }, { status: 500 })
    }

    return NextResponse.json({
      success: true,
      files: result.files ?? [],
    })

  } catch (error) {
    console.error('Impact error:', error)
    return NextResponse.json({ error: error.message || 'Something went wrong' }, { status: 500 })
  }
}
