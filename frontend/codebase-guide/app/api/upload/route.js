import { NextResponse } from 'next/server'
import { writeFile, mkdir } from 'fs/promises'
import path from 'path'

// Directory where uploaded files will be stored
const UPLOAD_DIR = path.join(process.cwd(), 'uploaded_repos')

export async function POST(request) {
  try {
    const formData = await request.formData()
    const files = formData.getAll('files')

    if (!files || files.length === 0) {
      return NextResponse.json(
        { error: 'No files received' },
        { status: 400 }
      )
    }

    // Create a timestamped folder for this upload session
    // so multiple uploads don't overwrite each other
    const sessionId = Date.now().toString()
    const sessionDir = path.join(UPLOAD_DIR, sessionId)
    await mkdir(sessionDir, { recursive: true })

    const savedFiles = []

    for (const file of files) {
      const bytes = await file.arrayBuffer()
      const buffer = Buffer.from(bytes)

      // Preserve the original filename
      const filename = file.name
      const filepath = path.join(sessionDir, filename)

      // Some uploaded files may have nested paths (e.g. src/components/Button.jsx)
      // This ensures those subdirectories get created too
      const fileDir = path.dirname(filepath)
      await mkdir(fileDir, { recursive: true })

      await writeFile(filepath, buffer)
      savedFiles.push({
        name: filename,
        size: file.size,
        path: filepath,
      })
    }

    return NextResponse.json({
      success: true,
      sessionId,
      fileCount: savedFiles.length,
      files: savedFiles.map(f => ({ name: f.name, size: f.size })),
      message: `${savedFiles.length} file${savedFiles.length > 1 ? 's' : ''} uploaded successfully`,
    })

  } catch (error) {
    console.error('Upload error:', error)
    return NextResponse.json(
      { error: 'Failed to save files', details: error.message },
      { status: 500 }
    )
  }
}
