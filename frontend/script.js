const generateBtn = document.getElementById('generateBtn');
const recipeOutput = document.getElementById('recipeOutput');
const loading = document.getElementById('loading');

generateBtn.addEventListener('click', async () => {
    const input = document.getElementById('ingredientsInput').value;
    const ingredients = input.split(',').map(i => i.trim()).filter(i => i !== "");

    if (ingredients.length === 0) {
        alert("Please enter at least one ingredient!");
        return;
    }

    // 1. Set up the dynamic thoughts
    const thoughts = [
        "Reviewing ingredients...",
        "Consulting flavor profiles...",
        "Preheating the digital oven...",
        "Adding a pinch of seasoning...",
        "Plating the final dish..."
    ];
    let thoughtIndex = 0;
    const thoughtElement = document.getElementById('thought-process');
    
    // Reset to the first thought
    thoughtElement.innerText = thoughts[0];
    
    // Show the loading graphic and clear old recipes
    loading.classList.remove('hidden');
    recipeOutput.innerHTML = '';

    // 2. Cycle the thoughts every 2 seconds (2000 milliseconds)
    const thoughtInterval = setInterval(() => {
        thoughtIndex = (thoughtIndex + 1) % thoughts.length;
        thoughtElement.innerText = thoughts[thoughtIndex];
    }, 2000);

    // 3. Make the actual API Call
    try {
        const response = await fetch('https://melg32pq1j.execute-api.us-east-1.amazonaws.com/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ingredients })
        });

        const data = await response.json();

        // 1. Stop the chef thought animation
        clearInterval(thoughtInterval);
        loading.classList.add('hidden');

        // 2. Handle Errors
        if (!response.ok) {
            recipeOutput.innerHTML = `<span style="color: #ef4444; font-weight: bold;">Oops!</span> ${data.error}`;
            return;
        }

        // 3. The Markdown Streaming Engine
        const rawMarkdown = data.recipe;
        recipeOutput.innerHTML = ''; // Clear the output div
        let currentIndex = 0;

        // We use an interval to simulate the AI typing out the response
        const typingSpeed = 65; // Milliseconds per frame. Lower = faster.
        const charsPerFrame = 9; // How many letters to reveal per frame

        const streamInterval = setInterval(() => {
            if (currentIndex < rawMarkdown.length) {
                // Grab the text from the start up to the current index
                const currentChunk = rawMarkdown.substring(0, currentIndex + charsPerFrame);
                
                // Parse the growing string into HTML on the fly!
                recipeOutput.innerHTML = marked.parse(currentChunk);
                
                currentIndex += charsPerFrame;
            } else {
                // Once finished, clear the interval and ensure a final clean parse
                clearInterval(streamInterval);
                recipeOutput.innerHTML = marked.parse(rawMarkdown);
            }
        }, typingSpeed);
        
    } catch (error) {
        clearInterval(thoughtInterval);
        loading.classList.add('hidden');
        recipeOutput.innerHTML = "Error: Could not connect to the server.";
    } finally {
        // 4. CRITICAL: Stop the thinking animation when the request finishes
        clearInterval(thoughtInterval);
        loading.classList.add('hidden');
    }
});

