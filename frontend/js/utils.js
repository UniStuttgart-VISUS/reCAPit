function timeFormat(tsec) {
    tsec = Math.floor(tsec);
    const hours = Math.floor(tsec / 3600)
    const minutes = Math.floor((tsec - 3600*hours) / 60);
    const seconds = tsec % 60;
    return (1 + hours).toString().padStart(2, '0') + ":" + minutes.toString().padStart(2, '0') + ":" + seconds.toString().padStart(2, '0');
}

    function interpolateColor(value, colorscheme) {
        // Clamp value between 0 and 1
        value = Math.max(0, Math.min(1, value));
        var colors;

        if (colorscheme === "BuGn")
            colors = ["#edf8fb","#b2e2e2","#66c2a4","#238b45"];
        else if (colorscheme === "BuPu")
            colors = ["#edf8fb","#b3cde3","#8c96c6","#88419d"];
        else if (colorscheme === "GnBu")
            colors = ["#f0f9e8","#bae4bc","#7bccc4","#2b8cbe"];
        else if (colorscheme === "OrRd")
            colors = ["#fef0d9","#fdcc8a","#fc8d59","#d7301f"];
        else if (colorscheme === "PuBuGn")
            colors = ["#f6eff7","#bdc9e1","#67a9cf","#02818a"];
        else if (colorscheme === "PuBu")
            colors = ["#f1eef6","#bdc9e1","#74a9cf","#0570b0"];
        else if (colorscheme === "PuRd")
            colors = ["#f1eef6","#d7b5d8","#df65b0","#ce1256"];
        else if (colorscheme === "RdPu")
            colors = ["#feebe2","#fbb4b9","#f768a1","#ae017e"]
        else if (colorscheme === "YlGnBu")
            colors = ["#ffffcc","#a1dab4","#41b6c4","#225ea8"];
            //colors = ["#fafafa","#a1dab4","#41b6c4","#225ea8"];

        // Determine the bin index (0 to 3)
        const binIndex = Math.min(Math.floor(value * colors.length), colors.length - 1);

        // Return the color corresponding to the bin
        return colors[binIndex];
    }