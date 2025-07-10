import type { NextApiRequest, NextApiResponse } from 'next'

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  console.log('API route hit') // Debug log
  
  if (req.method !== 'POST') {
    console.log('Method not allowed')
    return res.status(405).json({ error: 'Method not allowed' })
  }

  try {
    console.log('Request body:', req.body)
    
    const { message } = req.body
    
    if (!message) {
      console.log('Message missing')
      return res.status(400).json({ error: 'Message is required' })
    }

    console.log('Forwarding to FastAPI:', message)
    const response = await fetch('http://localhost:8000/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error('Backend error:', errorText)
      throw new Error(errorText || 'Backend request failed')
    }

    const data = await response.json()
    console.log('Response from FastAPI:', data)
    return res.status(200).json(data)
    
  } catch (error) {
    console.error('API error:', error)
    return res.status(500).json({ 
      error: error instanceof Error ? error.message : 'Internal server error'
    })
  }
}