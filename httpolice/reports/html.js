'use strict';

function setupNotices() {
    var i, button, notice, notices = document.querySelectorAll('.notice');

    for (i = 0; i < notices.length; i += 1) {
        notice = notices[i];

        // Collapse initially.
        notice.classList.add('collapsed');

        // Add the "explain" button.
        button = document.createElement('button');
        button.setAttribute('type', 'button');
        button.textContent = 'explain';
        button.addEventListener('click', onButtonClick);
        notice.insertBefore(button, notices[i].firstChild);

        // Set up highlights.
        notice.addEventListener('mouseover', highlightReferences);
        notice.addEventListener('mouseout', clearHighlights);
    }
}

function onButtonClick() {
    this.parentElement.classList.toggle('collapsed');
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

function toggleRemarks(show) {
    var i, remarks = document.querySelectorAll('.message-remark');
    for (i = 0; i < remarks.length; i += 1) {
        remarks[i].hidden = !show;
    }
}

function onOptionsSubmit(event) {
    var boringNotices =
            document.getElementById('boringNotices').value.split(/\s+/),
        hideBoringNotices =
            document.getElementById('hideBoringNotices').checked,
        hideBoringExchanges =
            document.getElementById('hideBoringExchanges').checked,
        showRemarks = document.getElementById('showRemarks').checked,
        i, exchanges, exchange, isBoringExchange,
        j, notices, notice, severity, ident, isBoringNotice;

    event.preventDefault();

    exchanges = document.querySelectorAll('.exchange');
    for (i = 0; i < exchanges.length; i += 1) {
        exchange = exchanges[i];
        isBoringExchange = true;
        notices = exchange.querySelectorAll('.notice');
        for (j = 0; j < notices.length; j += 1) {
            notice = notices[j];
            severity = notice.querySelector('.severity').textContent;
            ident = notice.querySelector('.ident').textContent;
            isBoringNotice = (boringNotices.indexOf(severity) > -1 ||
                              boringNotices.indexOf(ident) > -1);
            notice.hidden = (hideBoringNotices && isBoringNotice);
            if (!isBoringNotice && severity !== 'D') {
                isBoringExchange = false;
            }
        }
        exchange.hidden = (hideBoringExchanges && isBoringExchange);
    }

    toggleRemarks(showRemarks);
}

function installOptions() {
    var div, button, form,
        p1, label1, input1,
        p2, submit;

    div = document.createElement('div');
    div.classList.add('options');
    div.classList.add('collapsed');

    button = document.createElement('button');
    button.type = 'button';
    button.textContent = 'options';
    button.addEventListener('click', onButtonClick);
    div.appendChild(button);

    form = document.createElement('form');
    form.addEventListener('submit', onOptionsSubmit);
    div.appendChild(form);

    p1 = document.createElement('p');
    form.appendChild(p1);

    label1 = document.createElement('label');
    label1.htmlFor = 'boringNotices';
    label1.textContent = 'Boring notices:';
    p1.appendChild(label1);

    input1 = document.createElement('input');
    input1.type = 'text';
    input1.name = 'boringNotices';
    input1.id = input1.name;
    input1.placeholder = 'example: 1089 1135 C';
    p1.appendChild(input1);

    function addCheckboxRow(id, text, title) {
        var p, input, label;

        p = document.createElement('p');
        form.appendChild(p);

        input = document.createElement('input');
        input.type = 'checkbox';
        input.name = id;
        input.id = id;
        p.appendChild(input);

        label = document.createElement('label');
        label.htmlFor = id;
        label.textContent = text;
        p.appendChild(label);

        if (title) {
            input.title = title;
            label.title = title;
        }
    }

    addCheckboxRow('hideBoringNotices', 'Hide boring notices');
    addCheckboxRow('hideBoringExchanges', 'Hide boring exchanges',
        'Hide exchanges that have no notices, ' +
        'or only debug and boring notices');
    addCheckboxRow('showRemarks', 'Show remarks',
        'Remarks may contain the input filenames ' +
        'or other useful information.');

    p2 = document.createElement('p');
    form.appendChild(p2);

    submit = document.createElement('input');
    submit.type = 'submit';
    submit.value = 'Apply';
    p2.appendChild(submit);

    document.body.insertBefore(div, document.querySelector('h1'));
}

document.addEventListener('DOMContentLoaded', function () {
    setupNotices();
    toggleRemarks(false);
    installOptions();
});
