
const CATEGORICAL = {
  "Set1": ["#e41a1c","#377eb8","#4daf4a","#984ea3","#ff7f00","#ffff33","#a65628","#f781bf","#999999"],
  "Set2": ["#66c2a5","#fc8d62","#8da0cb","#e78ac3","#a6d854","#ffd92f","#e5c494","#b3b3b3"],
  "Set3": ["#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69","#fccde5","#d9d9d9","#bc80bd","#ccebc5","#ffed6f"],
  "Paired": ["#a6cee3","#1f78b4","#b2df8a","#33a02c","#fb9a99","#e31a1c","#fdbf6f","#ff7f00","#cab2d6","#6a3d9a","#ffff99","#b15928"],
  "Accent": ["#7fc97f","#beaed4","#fdc086","#ffff99","#386cb0","#f0027f","#bf5b17","#666666"],
  "Tableau10": ["#4e79a7","#f28e2c","#e15759","#76b7b2","#59a14f","#edc949","#af7aa1","#ff9da7","#9c755f","#bab0ab"],
  "Category10": ["#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd","#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf"],
  "Observable10": ["#4269d0","#efb118","#ff725c","#6cc5b0","#3ca951","#ff8ab7","#a463f2","#97bbf5","#9c6b4e","#9498a0"],
  "Purples": ["#f2f0f7","#dadaeb","#bcbddc","#9e9ac8","#756bb1","#54278f"],
  "Greens": ["#edf8e9","#c7e9c0","#a1d99b","#74c476","#31a354","#006d2c"],
  "Blues": ["#eff3ff","#c6dbef","#9ecae1","#6baed6","#3182bd","#08519c"],
  "Oranges": ["#feedde","#fdd0a2","#fdae6b","#fd8d3c","#e6550d","#a63603"],
  "Greys": ["#f7f7f7","#d9d9d9","#bdbdbd","#969696","#636363","#252525"],
  "Reds": ["#fee5d9","#fcbba1","#fc9272","#fb6a4a","#de2d26","#a50f15"]
}

const CONTINUOUS = [
  "CET_L8",
  "CET_L9",
  "CET_L10",
  "CET_L11",
  "CET_L12",
  "CET_L13",
  "CET_L14",
  "CET_L15",
  "CET_L16",
  "CET_L17",
  "CET_L18",
  "CET_L19",
  "CET_L20"
]

function createColorscheme(domain, colorscheme) {
    var colors = CATEGORICAL[colorscheme]
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
