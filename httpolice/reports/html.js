/* jshint browser: true */
/* jshint -W097 */

'use strict';

function collapseAll() {
    var i, elems = document.querySelectorAll('.notice');
    for (i = 0; i < elems.length; i += 1) {
        elems[i].classList.add('collapsed');
    }
}

function onButtonClick() {
    /* jshint -W040 */
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
    /* jshint -W040 */
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

function onOptionsSubmit(event) {
    var boringNotices =
            document.getElementById('boringNotices').value.split(/\s+/),
        hideBoringNotices =
            document.getElementById('hideBoringNotices').checked,
        hideBoringExchanges =
            document.getElementById('hideBoringExchanges').checked,
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
}

function installOptions() {
    var div, button, form,
        p1, label1, input1,
        p2, label2, input2,
        p3, label3, input3,
        p4, submit;

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

    p2 = document.createElement('p');
    form.appendChild(p2);

    input2 = document.createElement('input');
    input2.type = 'checkbox';
    input2.name = 'hideBoringNotices';
    input2.id = input2.name;
    p2.appendChild(input2);

    label2 = document.createElement('label');
    label2.htmlFor = 'hideBoringNotices';
    label2.textContent = 'Hide boring notices';
    p2.appendChild(label2);

    p3 = document.createElement('p');
    form.appendChild(p3);

    input3 = document.createElement('input');
    input3.type = 'checkbox';
    input3.name = 'hideBoringExchanges';
    input3.id = input3.name;
    input3.title = 'Hide exchanges that have no notices, ' +
        'or only debug and boring notices';
    p3.appendChild(input3);

    label3 = document.createElement('label');
    label3.htmlFor = 'hideBoringExchanges';
    label3.textContent = 'Hide boring exchanges';
    label3.title = input3.title;
    p3.appendChild(label3);

    p4 = document.createElement('p');
    form.appendChild(p4);

    submit = document.createElement('input');
    submit.type = 'submit';
    submit.value = 'Apply';
    p4.appendChild(submit);

    document.body.insertBefore(div, document.querySelector('h1'));
}

document.addEventListener('DOMContentLoaded', function () {
    collapseAll();
    installButtons();
    installHovers();
    installOptions();
});
