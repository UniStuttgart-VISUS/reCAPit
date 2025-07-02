
function createColorscheme(domain, colors) {
    var step = Math.floor(colors.length / domain.length);

    if (step == 0) {
        console.log("Error: Not enough colors for all domains!");
        const fill_colors = Array.from({length: domain.length - colors.length}, () => "#000");
        colors = colors.concat(fill_colors);
        step = 1
    }

    const map = new Map();

    for (let idx = 0; idx < domain.length; idx++) {
        map.set(domain[idx], colors[idx*step]);
    }
    return map;
}

function timeFormat(tsec) {
    tsec = Math.floor(tsec);
    const hours = Math.floor(tsec / 3600)
    const minutes = Math.floor((tsec - 3600*hours) / 60);
    const seconds = tsec % 60;
    return (1 + hours).toString().padStart(2, '0') + ":" + minutes.toString().padStart(2, '0') + ":" + seconds.toString().padStart(2, '0');
}
