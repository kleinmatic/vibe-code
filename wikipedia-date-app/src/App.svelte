<script>
  import { findArticleWithDate } from './lib/wikipedia.js';

  let dateInput = '';
  let loading = false;
  let result = null;
  let error = null;
  let progress = '';

  async function handleSubmit() {
    if (!dateInput.trim()) return;

    loading = true;
    error = null;
    result = null;
    progress = '';

    try {
      const data = await findArticleWithDate(dateInput, (msg) => {
        progress = msg;
      });
      result = data;
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
      progress = '';
    }
  }

  function handleKeyPress(event) {
    if (event.key === 'Enter') {
      handleSubmit();
    }
  }

  function searchAgain() {
    // Re-run the same search for a different random result
    handleSubmit();
  }

  function reset() {
    result = null;
    error = null;
    dateInput = '';
  }
</script>

<main>
  <div class="container">
    <header>
      <h1>Wikipedia Date Finder</h1>
      <p class="subtitle">Discover random Wikipedia articles from any date in history</p>
    </header>

    <div class="input-section">
      <input
        type="text"
        bind:value={dateInput}
        on:keypress={handleKeyPress}
        placeholder="Enter a date (e.g., 11/20, July 4, or 11/20/1968)"
        disabled={loading}
      />
      <button on:click={handleSubmit} disabled={loading || !dateInput.trim()}>
        {loading ? 'Searching...' : 'Find Article'}
      </button>
    </div>

    {#if progress}
      <div class="progress">{progress}</div>
    {/if}

    {#if error}
      <div class="error">
        <strong>Error:</strong> {error}
      </div>
    {/if}

    {#if result}
      <div class="result">
        <div class="result-header">
          <h2>{result.article}</h2>
          <button class="reset-button" on:click={searchAgain}>Search Again</button>
        </div>

        <div class="meta">
          <span class="method">{result.method}</span>
        </div>

        {#if result.context}
          <div class="context">
            <strong>Context:</strong>
            <p>{result.context}</p>
          </div>
        {/if}

        <a
          href="https://en.wikipedia.org/wiki/{result.article.replace(/ /g, '_')}"
          target="_blank"
          rel="noopener noreferrer"
          class="wiki-link"
        >
          Read on Wikipedia →
        </a>
      </div>
    {/if}

    <footer>
      <p class="hint">
        Try formats like: <code>11/20</code>, <code>July 4</code>, <code>11/20/1968</code>,
        <code>2024-01-15</code>, or <code>December 25, 2023</code>
      </p>
    </footer>
  </div>
</main>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
  }

  main {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    padding: 2rem;
  }

  .container {
    max-width: 700px;
    width: 100%;
    background: white;
    border-radius: 20px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    padding: 3rem;
    animation: fadeIn 0.5s ease-in;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  header {
    text-align: center;
    margin-bottom: 2rem;
  }

  h1 {
    margin: 0;
    font-size: 2.5rem;
    color: #333;
    font-weight: 700;
  }

  .subtitle {
    margin: 0.5rem 0 0 0;
    color: #666;
    font-size: 1.1rem;
  }

  .input-section {
    display: flex;
    gap: 0.75rem;
    margin-bottom: 1.5rem;
  }

  input {
    flex: 1;
    padding: 1rem;
    font-size: 1rem;
    border: 2px solid #e0e0e0;
    border-radius: 10px;
    transition: all 0.3s;
  }

  input:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }

  input:disabled {
    background: #f5f5f5;
    cursor: not-allowed;
  }

  button {
    padding: 1rem 2rem;
    font-size: 1rem;
    font-weight: 600;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.3s;
    white-space: nowrap;
  }

  button:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
  }

  button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .progress {
    padding: 1rem;
    background: #f0f0f0;
    border-radius: 10px;
    text-align: center;
    color: #666;
    margin-bottom: 1rem;
    animation: pulse 1.5s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
  }

  .error {
    padding: 1rem;
    background: #fee;
    border-left: 4px solid #f44;
    border-radius: 10px;
    color: #c33;
    margin-bottom: 1rem;
  }

  .result {
    padding: 2rem;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    border-radius: 15px;
    margin-bottom: 1.5rem;
    animation: slideIn 0.5s ease-out;
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateX(-20px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  .result-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .result h2 {
    margin: 0;
    color: #333;
    font-size: 1.8rem;
    flex: 1;
  }

  .reset-button {
    padding: 0.5rem 1rem;
    font-size: 0.9rem;
    background: #666;
  }

  .meta {
    margin-bottom: 1rem;
  }

  .method {
    display: inline-block;
    padding: 0.4rem 0.8rem;
    background: rgba(102, 126, 234, 0.2);
    color: #667eea;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
  }

  .context {
    margin: 1.5rem 0;
    padding: 1rem;
    background: white;
    border-radius: 10px;
    border-left: 4px solid #667eea;
  }

  .context strong {
    color: #667eea;
    display: block;
    margin-bottom: 0.5rem;
  }

  .context p {
    margin: 0;
    color: #444;
    line-height: 1.6;
  }

  .wiki-link {
    display: inline-block;
    padding: 0.75rem 1.5rem;
    background: white;
    color: #667eea;
    text-decoration: none;
    border-radius: 10px;
    font-weight: 600;
    transition: all 0.3s;
    border: 2px solid #667eea;
  }

  .wiki-link:hover {
    background: #667eea;
    color: white;
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
  }

  footer {
    text-align: center;
    color: #666;
    font-size: 0.9rem;
    line-height: 1.6;
  }

  footer p {
    margin: 0.5rem 0;
  }

  .hint {
    font-size: 0.85rem;
    color: #999;
  }

  code {
    background: #f0f0f0;
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
    font-family: 'Monaco', 'Courier New', monospace;
    font-size: 0.9em;
  }

  @media (max-width: 600px) {
    .container {
      padding: 2rem;
    }

    h1 {
      font-size: 2rem;
    }

    .input-section {
      flex-direction: column;
    }

    button {
      width: 100%;
    }

    .result-header {
      flex-direction: column;
    }

    .reset-button {
      width: 100%;
    }
  }
</style>
