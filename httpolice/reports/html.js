'use strict';

function collapseAll() {
    var i, elems = document.querySelectorAll('.notice');
    for (i = 0; i < elems.length; i += 1) {
        elems[i].classList.add('collapsed');
    }
}

function onButtonClick() {
    this.parentElement.classList.toggle('collapsed');
}

function installButtons() {
    var i, button, notices = document.querySelectorAll('.notice');
    for (i = 0; i < notices.length; i += 1) {
        button = document.createElement('button');
        button.setAttribute('type', 'button');
        button.textContent = 'explain';
        button.addEventListener('click', onButtonClick);
        notices[i].insertBefore(button, notices[i].firstChild);
    }
}

function highlightReferences() {
    var i, referrers, refs, exchange, target;

    // Collect references from all contributing elements within this notice.
    referrers = this.querySelectorAll('[data-ref-to]');
    refs = [];
    for (i = 0; i < referrers.length; i += 1) {
        refs = refs.concat(
            referrers[i].getAttribute('data-ref-to').split(' ')
        );
    }

    // Traverse up to the closest exchange element.
    exchange = this;
    while (!exchange.classList.contains('exchange')) {
        exchange = exchange.parentElement;
    }

    // Add highlight to every referenced element within this exchange.
    // (``data-ref-id`` are only unique within an exchange.)
    for (i = 0; i < refs.length; i += 1) {
        target = exchange.querySelector('[data-ref-id="' + refs[i] + '"]');
        if (target !== null) {
            target.classList.add('highlight');
        }
    }
}

function clearHighlights() {
    var i, elems = document.querySelectorAll('.highlight');
    for (i = 0; i < elems.length; i += 1) {
        elems[i].classList.remove('highlight');
    }
}

function installHovers() {
    var i, notices = document.querySelectorAll('.notice');
    for (i = 0; i < notices.length; i += 1) {
        notices[i].addEventListener('mouseover', highlightReferences);
        notices[i].addEventListener('mouseout', clearHighlights);
    }
}

document.addEventListener('DOMContentLoaded', function () {
    collapseAll();
    installButtons();
    installHovers();
});
