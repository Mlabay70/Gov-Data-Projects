let map;
function getQueryParam(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name) || '';
}
function initMap() {
    map = new google.maps.Map(document.getElementById('map'), {
        center: { lat: 39.8283, lng: -98.5795 }, // Center of USA
        zoom: 4,
        mapId: '56e8e57a4150e1cdb6d56670' // <-- Replace with your actual Map ID
    });
    const zipcode = getQueryParam('zipcode');
    const state = getQueryParam('state');
    if (zipcode || state) {
        let apiUrl = `/api/buildings?zipcode=${encodeURIComponent(zipcode)}`;
        if (state) {
            apiUrl += `&state=${encodeURIComponent(state)}`;
        }
        fetch(apiUrl)
            .then(response => response.json())
            .then(buildings => {
                if (buildings.length > 0) {
                    const bounds = new google.maps.LatLngBounds();
                    const geocoder = new google.maps.Geocoder();
                    let geocodeCount = 0;
                    buildings.forEach(b => {
                        const fullAddress = `${b.address}, ${b.city}, ${b.state} ${b.zipcode}`;
                        geocoder.geocode({ address: fullAddress }, function(results, status) {
                            geocodeCount++;
                            if (status === 'OK' && results[0]) {
                                const iconDiv = document.createElement('div');
                                // Use green marker if available space > 0, else red
                                const available = b.available_sqft && parseFloat(b.available_sqft) > 0;
                                const markerColor = available ? 'green-dot.png' : 'red-dot.png';
                                iconDiv.innerHTML = `<img src="https://maps.google.com/mapfiles/ms/icons/${markerColor}" style="width:40px;height:40px;">`;
                                const marker = new google.maps.marker.AdvancedMarkerElement({
                                    map: map,
                                    position: results[0].geometry.location,
                                    title: b.name,
                                    content: iconDiv
                                });
                                let info = `<strong>${b.name}</strong><br>${fullAddress}`;
                                info += `<br><span>Build Date: ${b.construction_date || 'N/A'}</span>`;
                                if (available) {
                                    info += `<br><span style='color:green;font-weight:bold;'>Available Sq Ft: ${b.available_sqft}</span>`;
                                }
                                const infowindow = new google.maps.InfoWindow({ content: info });
                                marker.addListener('click', () => infowindow.open(map, marker));
                                bounds.extend(results[0].geometry.location);
                            }
                            // After all geocodes, fit bounds
                            if (geocodeCount === buildings.length && bounds.getNorthEast().lat() !== bounds.getSouthWest().lat()) {
                                map.fitBounds(bounds);
                            }
                        });
                    });
                } else {
                    alert('No buildings found for this zip code.');
                }
            });
    }
}
