function timeFormat(tsec) {
    tsec = Math.floor(tsec);
    const hours = Math.floor(tsec / 3600)
    const minutes = Math.floor((tsec - 3600*hours) / 60);
    const seconds = tsec % 60;
    return (1 + hours).toString().padStart(2, '0') + ":" + minutes.toString().padStart(2, '0') + ":" + seconds.toString().padStart(2, '0');
}
