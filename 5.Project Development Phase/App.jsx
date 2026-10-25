import { useState } from 'react'
import './App.css'

function App() {
  const [ingredients, setIngredients] = useState('paneer, spinach, cherry tomato')
  const [result, setResult] = useState('')
  const [loading, setLoading] = useState(false)

  async function generateRecipe(e) {
    e.preventDefault()
    setLoading(true)
    setResult('')

try {
  const formData = new FormData()
formData.append('text_input', ingredients)

const response = await fetch(
  'http://127.0.0.1:8000/api/kitchen-assistant/generate-recipe',
  {
    method: 'POST',
    body: formData
  }
)

  const text = await response.text()
  setResult(`HTTP ${response.status}\n${text}`)
} catch (error) {
  setResult(`Browser connection error: ${error.message}`)
} finally {
  setLoading(false)
}
  }

  return (
    <main className="foodverse">
      <header><h2>🥗 Foodverse <span>AI</span></h2></header>
      <section className="hero">
        <p>YOUR SMART KITCHEN COMPANION</p>
        <h1>Cook smarter.<br /><span>Eat better.</span></h1>
        <p>Turn the ingredients in your kitchen into your next meal.</p>
      </section>
      <section className="recipe-card">
        <h2>✨ AI Recipe Generator</h2>
        <form onSubmit={generateRecipe}>
          <label htmlFor="ingredients">Available ingredients (separate with commas)</label>
          <textarea id="ingredients" value={ingredients}
            onChange={e => setIngredients(e.target.value)} required />
          <button type="submit" disabled={loading}>
            {loading ? 'Generating...' : 'Generate my recipe →'}
          </button>
        </form>
        {result && (
  <div className="result">
    <h3>🍽️ Your Recipe</h3>
    <pre>{(() => {
      try {
        const data = JSON.parse(result.replace(/^HTTP \d+\n/, ""))
        const formatted = Object.fromEntries(
          Object.entries(data).map(([key, value]) => [
            key === "dish_name" ? "Dish Name" :
            key === "ingredients" ? "Ingredients" :
            key,
            value
          ])
        )
        return JSON.stringify(formatted, null, 2)
      } catch {
        return result
      }
    })()}</pre>
  </div>
)}
      </section>
      <footer>Foodverse AI · Multimodal Food Intelligence Agent</footer>
    </main>
  )
}

export default App