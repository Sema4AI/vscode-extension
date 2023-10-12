"use strict";
var Ts = Object.defineProperty,
    Os = Object.defineProperties;
var Ms = Object.getOwnPropertyDescriptors;
var dr = Object.getOwnPropertySymbols;
var Rs = Object.prototype.hasOwnProperty,
    Ns = Object.prototype.propertyIsEnumerable;
var pr = (t, A, e) => (A in t ? Ts(t, A, { enumerable: !0, configurable: !0, writable: !0, value: e }) : (t[A] = e)),
    DA = (t, A) => {
        for (var e in A || (A = {})) Rs.call(A, e) && pr(t, e, A[e]);
        if (dr) for (var e of dr(A)) Ns.call(A, e) && pr(t, e, A[e]);
        return t;
    },
    Ae = (t, A) => Os(t, Ms(A));
var UA = (t, A, e) =>
    new Promise((r, n) => {
        var s = (a) => {
                try {
                    i(e.next(a));
                } catch (o) {
                    n(o);
                }
            },
            B = (a) => {
                try {
                    i(e.throw(a));
                } catch (o) {
                    n(o);
                }
            },
            i = (a) => (a.done ? r(a.value) : Promise.resolve(a.value).then(s, B));
        i((e = e.apply(t, A)).next());
    });
let aA, ur;
function Gs(t, A) {
    if (t.nodeType !== Node.ELEMENT_NODE) throw new Error("Can't generate CSS selector for non-element node type.");
    if (t.tagName.toLowerCase() === "html") return "html";
    const e = {
        root: document.body,
        idName: (n) => !0,
        className: (n) => !0,
        tagName: (n) => !0,
        attr: (n, s) => !1,
        seedMinLength: 1,
        optimizedMinLength: 2,
        threshold: 1e3,
        maxNumberOfTries: 1e4,
    };
    (aA = DA(DA({}, e), A)), (ur = Vs(aA.root, e));
    let r = pe(t, "all", () => pe(t, "two", () => pe(t, "one", () => pe(t, "none"))));
    if (r) {
        const n = Kn(bn(r, t));
        return n.length > 0 && (r = n[0]), ct(r);
    } else throw new Error("Selector was not found.");
}
function Vs(t, A) {
    return t.nodeType === Node.DOCUMENT_NODE ? t : t === A.root ? t.ownerDocument : t;
}
function pe(t, A, e) {
    let r = null,
        n = [],
        s = t,
        B = 0;
    for (; s; ) {
        let i = He(ks(s)) || He(...Ps(s)) || He(..._s(s)) || He(Xs(s)) || [vr()];
        const a = Js(s);
        if (A == "all") a && (i = i.concat(i.filter(dt).map((o) => Ee(o, a))));
        else if (A == "two") (i = i.slice(0, 1)), a && (i = i.concat(i.filter(dt).map((o) => Ee(o, a))));
        else if (A == "one") {
            const [o] = (i = i.slice(0, 1));
            a && dt(o) && (i = [Ee(o, a)]);
        } else A == "none" && ((i = [vr()]), a && (i = [Ee(i[0], a)]));
        for (let o of i) o.level = B;
        if ((n.push(i), n.length >= aA.seedMinLength && ((r = Er(n, e)), r))) break;
        (s = s.parentElement), B++;
    }
    return r || (r = Er(n, e)), !r && e ? e() : r;
}
function Er(t, A) {
    const e = Kn(Ln(t));
    if (e.length > aA.threshold) return A ? A() : null;
    for (let r of e) if (yn(r)) return r;
    return null;
}
function ct(t) {
    let A = t[0],
        e = A.name;
    for (let r = 1; r < t.length; r++) {
        const n = t[r].level || 0;
        A.level === n - 1 ? (e = `${t[r].name} > ${e}`) : (e = `${t[r].name} ${e}`), (A = t[r]);
    }
    return e;
}
function Hr(t) {
    return t.map((A) => A.penalty).reduce((A, e) => A + e, 0);
}
function yn(t) {
    const A = ct(t);
    switch (ur.querySelectorAll(A).length) {
        case 0:
            throw new Error(`Can't select any node with this selector: ${A}`);
        case 1:
            return !0;
        default:
            return !1;
    }
}
function ks(t) {
    const A = t.getAttribute("id");
    return A && aA.idName(A) ? { name: "#" + CSS.escape(A), penalty: 0 } : null;
}
function Ps(t) {
    return Array.from(t.attributes)
        .filter((e) => aA.attr(e.name, e.value))
        .map((e) => ({ name: `[${CSS.escape(e.name)}="${CSS.escape(e.value)}"]`, penalty: 0.5 }));
}
function _s(t) {
    return Array.from(t.classList)
        .filter(aA.className)
        .map((e) => ({ name: "." + CSS.escape(e), penalty: 1 }));
}
function Xs(t) {
    const A = t.tagName.toLowerCase();
    return aA.tagName(A) ? { name: A, penalty: 2 } : null;
}
function vr() {
    return { name: "*", penalty: 3 };
}
function Js(t) {
    const A = t.parentNode;
    if (!A) return null;
    let e = A.firstChild;
    if (!e) return null;
    let r = 0;
    for (; e && (e.nodeType === Node.ELEMENT_NODE && r++, e !== t); ) e = e.nextSibling;
    return r;
}
function Ee(t, A) {
    return { name: t.name + `:nth-child(${A})`, penalty: t.penalty + 1 };
}
function dt(t) {
    return t.name !== "html" && !t.name.startsWith("#");
}
function He(...t) {
    const A = t.filter(Ys);
    return A.length > 0 ? A : null;
}
function Ys(t) {
    return t != null;
}
function* Ln(t, A = []) {
    if (t.length > 0) for (let e of t[0]) yield* Ln(t.slice(1, t.length), A.concat(e));
    else yield A;
}
function Kn(t) {
    return [...t].sort((A, e) => Hr(A) - Hr(e));
}
function* bn(t, A, e = { counter: 0, visited: new Map() }) {
    if (t.length > 2 && t.length > aA.optimizedMinLength)
        for (let r = 1; r < t.length - 1; r++) {
            if (e.counter > aA.maxNumberOfTries) return;
            e.counter += 1;
            const n = [...t];
            n.splice(r, 1);
            const s = ct(n);
            if (e.visited.has(s)) return;
            yn(n) && Ws(n, A) && (yield n, e.visited.set(s, !0), yield* bn(n, A, e));
        }
}
function Ws(t, A) {
    return ur.querySelector(ct(t)) === A;
}
/*!
 * html2canvas 1.4.1 <https://html2canvas.hertzen.com>
 * Copyright (c) 2022 Niklas von Hertzen <https://hertzen.com>
 * Released under MIT License
 */ /*! *****************************************************************************
Copyright (c) Microsoft Corporation.

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.
***************************************************************************** */ var Pt = function (t, A) {
    return (
        (Pt =
            Object.setPrototypeOf ||
            ({ __proto__: [] } instanceof Array &&
                function (e, r) {
                    e.__proto__ = r;
                }) ||
            function (e, r) {
                for (var n in r) Object.prototype.hasOwnProperty.call(r, n) && (e[n] = r[n]);
            }),
        Pt(t, A)
    );
};
function sA(t, A) {
    if (typeof A != "function" && A !== null)
        throw new TypeError("Class extends value " + String(A) + " is not a constructor or null");
    Pt(t, A);
    function e() {
        this.constructor = t;
    }
    t.prototype = A === null ? Object.create(A) : ((e.prototype = A.prototype), new e());
}
var _t = function () {
    return (
        (_t =
            Object.assign ||
            function (A) {
                for (var e, r = 1, n = arguments.length; r < n; r++) {
                    e = arguments[r];
                    for (var s in e) Object.prototype.hasOwnProperty.call(e, s) && (A[s] = e[s]);
                }
                return A;
            }),
        _t.apply(this, arguments)
    );
};
function J(t, A, e, r) {
    function n(s) {
        return s instanceof e
            ? s
            : new e(function (B) {
                  B(s);
              });
    }
    return new (e || (e = Promise))(function (s, B) {
        function i(c) {
            try {
                o(r.next(c));
            } catch (l) {
                B(l);
            }
        }
        function a(c) {
            try {
                o(r.throw(c));
            } catch (l) {
                B(l);
            }
        }
        function o(c) {
            c.done ? s(c.value) : n(c.value).then(i, a);
        }
        o((r = r.apply(t, A || [])).next());
    });
}
function _(t, A) {
    var e = {
            label: 0,
            sent: function () {
                if (s[0] & 1) throw s[1];
                return s[1];
            },
            trys: [],
            ops: [],
        },
        r,
        n,
        s,
        B;
    return (
        (B = { next: i(0), throw: i(1), return: i(2) }),
        typeof Symbol == "function" &&
            (B[Symbol.iterator] = function () {
                return this;
            }),
        B
    );
    function i(o) {
        return function (c) {
            return a([o, c]);
        };
    }
    function a(o) {
        if (r) throw new TypeError("Generator is already executing.");
        for (; e; )
            try {
                if (
                    ((r = 1),
                    n &&
                        (s = o[0] & 2 ? n.return : o[0] ? n.throw || ((s = n.return) && s.call(n), 0) : n.next) &&
                        !(s = s.call(n, o[1])).done)
                )
                    return s;
                switch (((n = 0), s && (o = [o[0] & 2, s.value]), o[0])) {
                    case 0:
                    case 1:
                        s = o;
                        break;
                    case 4:
                        return e.label++, { value: o[1], done: !1 };
                    case 5:
                        e.label++, (n = o[1]), (o = [0]);
                        continue;
                    case 7:
                        (o = e.ops.pop()), e.trys.pop();
                        continue;
                    default:
                        if (((s = e.trys), !(s = s.length > 0 && s[s.length - 1]) && (o[0] === 6 || o[0] === 2))) {
                            e = 0;
                            continue;
                        }
                        if (o[0] === 3 && (!s || (o[1] > s[0] && o[1] < s[3]))) {
                            e.label = o[1];
                            break;
                        }
                        if (o[0] === 6 && e.label < s[1]) {
                            (e.label = s[1]), (s = o);
                            break;
                        }
                        if (s && e.label < s[2]) {
                            (e.label = s[2]), e.ops.push(o);
                            break;
                        }
                        s[2] && e.ops.pop(), e.trys.pop();
                        continue;
                }
                o = A.call(t, e);
            } catch (c) {
                (o = [6, c]), (n = 0);
            } finally {
                r = s = 0;
            }
        if (o[0] & 5) throw o[1];
        return { value: o[0] ? o[1] : void 0, done: !0 };
    }
}
function ve(t, A, e) {
    if (e || arguments.length === 2)
        for (var r = 0, n = A.length, s; r < n; r++)
            (s || !(r in A)) && (s || (s = Array.prototype.slice.call(A, 0, r)), (s[r] = A[r]));
    return t.concat(s || A);
}
var fA = (function () {
        function t(A, e, r, n) {
            (this.left = A), (this.top = e), (this.width = r), (this.height = n);
        }
        return (
            (t.prototype.add = function (A, e, r, n) {
                return new t(this.left + A, this.top + e, this.width + r, this.height + n);
            }),
            (t.fromClientRect = function (A, e) {
                return new t(e.left + A.windowBounds.left, e.top + A.windowBounds.top, e.width, e.height);
            }),
            (t.fromDOMRectList = function (A, e) {
                var r = Array.from(e).find(function (n) {
                    return n.width !== 0;
                });
                return r ? new t(r.left + A.windowBounds.left, r.top + A.windowBounds.top, r.width, r.height) : t.EMPTY;
            }),
            (t.EMPTY = new t(0, 0, 0, 0)),
            t
        );
    })(),
    lt = function (t, A) {
        return fA.fromClientRect(t, A.getBoundingClientRect());
    },
    Zs = function (t) {
        var A = t.body,
            e = t.documentElement;
        if (!A || !e) throw new Error("Unable to get document size");
        var r = Math.max(
                Math.max(A.scrollWidth, e.scrollWidth),
                Math.max(A.offsetWidth, e.offsetWidth),
                Math.max(A.clientWidth, e.clientWidth)
            ),
            n = Math.max(
                Math.max(A.scrollHeight, e.scrollHeight),
                Math.max(A.offsetHeight, e.offsetHeight),
                Math.max(A.clientHeight, e.clientHeight)
            );
        return new fA(0, 0, r, n);
    },
    gt = function (t) {
        for (var A = [], e = 0, r = t.length; e < r; ) {
            var n = t.charCodeAt(e++);
            if (n >= 55296 && n <= 56319 && e < r) {
                var s = t.charCodeAt(e++);
                (s & 64512) === 56320 ? A.push(((n & 1023) << 10) + (s & 1023) + 65536) : (A.push(n), e--);
            } else A.push(n);
        }
        return A;
    },
    O = function () {
        for (var t = [], A = 0; A < arguments.length; A++) t[A] = arguments[A];
        if (String.fromCodePoint) return String.fromCodePoint.apply(String, t);
        var e = t.length;
        if (!e) return "";
        for (var r = [], n = -1, s = ""; ++n < e; ) {
            var B = t[n];
            B <= 65535 ? r.push(B) : ((B -= 65536), r.push((B >> 10) + 55296, (B % 1024) + 56320)),
                (n + 1 === e || r.length > 16384) && ((s += String.fromCharCode.apply(String, r)), (r.length = 0));
        }
        return s;
    },
    Ir = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",
    qs = typeof Uint8Array == "undefined" ? [] : new Uint8Array(256);
for (var Ie = 0; Ie < Ir.length; Ie++) qs[Ir.charCodeAt(Ie)] = Ie;
var mr = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",
    se = typeof Uint8Array == "undefined" ? [] : new Uint8Array(256);
for (var me = 0; me < mr.length; me++) se[mr.charCodeAt(me)] = me;
var js = function (t) {
        var A = t.length * 0.75,
            e = t.length,
            r,
            n = 0,
            s,
            B,
            i,
            a;
        t[t.length - 1] === "=" && (A--, t[t.length - 2] === "=" && A--);
        var o =
                typeof ArrayBuffer != "undefined" &&
                typeof Uint8Array != "undefined" &&
                typeof Uint8Array.prototype.slice != "undefined"
                    ? new ArrayBuffer(A)
                    : new Array(A),
            c = Array.isArray(o) ? o : new Uint8Array(o);
        for (r = 0; r < e; r += 4)
            (s = se[t.charCodeAt(r)]),
                (B = se[t.charCodeAt(r + 1)]),
                (i = se[t.charCodeAt(r + 2)]),
                (a = se[t.charCodeAt(r + 3)]),
                (c[n++] = (s << 2) | (B >> 4)),
                (c[n++] = ((B & 15) << 4) | (i >> 2)),
                (c[n++] = ((i & 3) << 6) | (a & 63));
        return o;
    },
    zs = function (t) {
        for (var A = t.length, e = [], r = 0; r < A; r += 2) e.push((t[r + 1] << 8) | t[r]);
        return e;
    },
    $s = function (t) {
        for (var A = t.length, e = [], r = 0; r < A; r += 4)
            e.push((t[r + 3] << 24) | (t[r + 2] << 16) | (t[r + 1] << 8) | t[r]);
        return e;
    },
    RA = 5,
    Qr = 6 + 5,
    pt = 2,
    AB = Qr - RA,
    xn = 65536 >> RA,
    eB = 1 << RA,
    Et = eB - 1,
    tB = 1024 >> RA,
    rB = xn + tB,
    nB = rB,
    sB = 32,
    BB = nB + sB,
    iB = 65536 >> Qr,
    aB = 1 << AB,
    oB = aB - 1,
    yr = function (t, A, e) {
        return t.slice ? t.slice(A, e) : new Uint16Array(Array.prototype.slice.call(t, A, e));
    },
    cB = function (t, A, e) {
        return t.slice ? t.slice(A, e) : new Uint32Array(Array.prototype.slice.call(t, A, e));
    },
    lB = function (t, A) {
        var e = js(t),
            r = Array.isArray(e) ? $s(e) : new Uint32Array(e),
            n = Array.isArray(e) ? zs(e) : new Uint16Array(e),
            s = 24,
            B = yr(n, s / 2, r[4] / 2),
            i = r[5] === 2 ? yr(n, (s + r[4]) / 2) : cB(r, Math.ceil((s + r[4]) / 4));
        return new gB(r[0], r[1], r[2], r[3], B, i);
    },
    gB = (function () {
        function t(A, e, r, n, s, B) {
            (this.initialValue = A),
                (this.errorValue = e),
                (this.highStart = r),
                (this.highValueIndex = n),
                (this.index = s),
                (this.data = B);
        }
        return (
            (t.prototype.get = function (A) {
                var e;
                if (A >= 0) {
                    if (A < 55296 || (A > 56319 && A <= 65535))
                        return (e = this.index[A >> RA]), (e = (e << pt) + (A & Et)), this.data[e];
                    if (A <= 65535)
                        return (e = this.index[xn + ((A - 55296) >> RA)]), (e = (e << pt) + (A & Et)), this.data[e];
                    if (A < this.highStart)
                        return (
                            (e = BB - iB + (A >> Qr)),
                            (e = this.index[e]),
                            (e += (A >> RA) & oB),
                            (e = this.index[e]),
                            (e = (e << pt) + (A & Et)),
                            this.data[e]
                        );
                    if (A <= 1114111) return this.data[this.highValueIndex];
                }
                return this.errorValue;
            }),
            t
        );
    })(),
    Lr = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",
    uB = typeof Uint8Array == "undefined" ? [] : new Uint8Array(256);
for (var ye = 0; ye < Lr.length; ye++) uB[Lr.charCodeAt(ye)] = ye;
var QB =
        "KwAAAAAAAAAACA4AUD0AADAgAAACAAAAAAAIABAAGABAAEgAUABYAGAAaABgAGgAYgBqAF8AZwBgAGgAcQB5AHUAfQCFAI0AlQCdAKIAqgCyALoAYABoAGAAaABgAGgAwgDKAGAAaADGAM4A0wDbAOEA6QDxAPkAAQEJAQ8BFwF1AH0AHAEkASwBNAE6AUIBQQFJAVEBWQFhAWgBcAF4ATAAgAGGAY4BlQGXAZ8BpwGvAbUBvQHFAc0B0wHbAeMB6wHxAfkBAQIJAvEBEQIZAiECKQIxAjgCQAJGAk4CVgJeAmQCbAJ0AnwCgQKJApECmQKgAqgCsAK4ArwCxAIwAMwC0wLbAjAA4wLrAvMC+AIAAwcDDwMwABcDHQMlAy0DNQN1AD0DQQNJA0kDSQNRA1EDVwNZA1kDdQB1AGEDdQBpA20DdQN1AHsDdQCBA4kDkQN1AHUAmQOhA3UAdQB1AHUAdQB1AHUAdQB1AHUAdQB1AHUAdQB1AHUAdQB1AKYDrgN1AHUAtgO+A8YDzgPWAxcD3gPjA+sD8wN1AHUA+wMDBAkEdQANBBUEHQQlBCoEFwMyBDgEYABABBcDSARQBFgEYARoBDAAcAQzAXgEgASIBJAEdQCXBHUAnwSnBK4EtgS6BMIEyAR1AHUAdQB1AHUAdQCVANAEYABgAGAAYABgAGAAYABgANgEYADcBOQEYADsBPQE/AQEBQwFFAUcBSQFLAU0BWQEPAVEBUsFUwVbBWAAYgVgAGoFcgV6BYIFigWRBWAAmQWfBaYFYABgAGAAYABgAKoFYACxBbAFuQW6BcEFwQXHBcEFwQXPBdMF2wXjBeoF8gX6BQIGCgYSBhoGIgYqBjIGOgZgAD4GRgZMBmAAUwZaBmAAYABgAGAAYABgAGAAYABgAGAAYABgAGIGYABpBnAGYABgAGAAYABgAGAAYABgAGAAYAB4Bn8GhQZgAGAAYAB1AHcDFQSLBmAAYABgAJMGdQA9A3UAmwajBqsGqwaVALMGuwbDBjAAywbSBtIG1QbSBtIG0gbSBtIG0gbdBuMG6wbzBvsGAwcLBxMHAwcbByMHJwcsBywHMQcsB9IGOAdAB0gHTgfSBkgHVgfSBtIG0gbSBtIG0gbSBtIG0gbSBiwHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAdgAGAALAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAdbB2MHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsB2kH0gZwB64EdQB1AHUAdQB1AHUAdQB1AHUHfQdgAIUHjQd1AHUAlQedB2AAYAClB6sHYACzB7YHvgfGB3UAzgfWBzMB3gfmB1EB7gf1B/0HlQENAQUIDQh1ABUIHQglCBcDLQg1CD0IRQhNCEEDUwh1AHUAdQBbCGMIZAhlCGYIZwhoCGkIYwhkCGUIZghnCGgIaQhjCGQIZQhmCGcIaAhpCGMIZAhlCGYIZwhoCGkIYwhkCGUIZghnCGgIaQhjCGQIZQhmCGcIaAhpCGMIZAhlCGYIZwhoCGkIYwhkCGUIZghnCGgIaQhjCGQIZQhmCGcIaAhpCGMIZAhlCGYIZwhoCGkIYwhkCGUIZghnCGgIaQhjCGQIZQhmCGcIaAhpCGMIZAhlCGYIZwhoCGkIYwhkCGUIZghnCGgIaQhjCGQIZQhmCGcIaAhpCGMIZAhlCGYIZwhoCGkIYwhkCGUIZghnCGgIaQhjCGQIZQhmCGcIaAhpCGMIZAhlCGYIZwhoCGkIYwhkCGUIZghnCGgIaQhjCGQIZQhmCGcIaAhpCGMIZAhlCGYIZwhoCGkIYwhkCGUIZghnCGgIaQhjCGQIZQhmCGcIaAhpCGMIZAhlCGYIZwhoCGkIYwhkCGUIZghnCGgIaQhjCGQIZQhmCGcIaAhpCGMIZAhlCGYIZwhoCGkIYwhkCGUIZghnCGgIaQhjCGQIZQhmCGcIaAhpCGMIZAhlCGYIZwhoCGkIYwhkCGUIZghnCGgIaQhjCGQIZQhmCGcIaAhpCGMIZAhlCGYIZwhoCGkIYwhkCGUIZghnCGgIaQhjCGQIZQhmCGcIaAhpCGMIZAhlCGYIZwhoCGkIYwhkCGUIZghnCGgIaQhjCGQIZQhmCGcIaAhpCGMIZAhlCGYIZwhoCGkIYwhkCGUIZghnCGgIaQhjCGQIZQhmCGcIaAhpCGMIZAhlCGYIZwhoCGkIYwhkCGUIZghnCGgIaQhjCGQIZQhmCGcIaAhpCGMIZAhlCGYIZwhoCGkIYwhkCGUIZghnCGgIaQhjCGQIZQhmCGcIaAhpCGMIZAhlCGYIZwhoCGkIYwhkCGUIZghnCGgIcAh3CHoIMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwAIIIggiCCIIIggiCCIIIggiCCIIIggiCCIIIggiCCIIIggiCCIIIggiCCIIIggiCCIIIggiCCIIIggiCCIIIgggwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAALAcsBywHLAcsBywHLAcsBywHLAcsB4oILAcsB44I0gaWCJ4Ipgh1AHUAqgiyCHUAdQB1AHUAdQB1AHUAdQB1AHUAtwh8AXUAvwh1AMUIyQjRCNkI4AjoCHUAdQB1AO4I9gj+CAYJDgkTCS0HGwkjCYIIggiCCIIIggiCCIIIggiCCIIIggiCCIIIggiCCIIIggiCCIIIggiCCIIIggiCCIIIggiCCIIIggiCCIIIggiAAIAAAAFAAYABgAGIAXwBgAHEAdQBFAJUAogCyAKAAYABgAEIA4ABGANMA4QDxAMEBDwE1AFwBLAE6AQEBUQF4QkhCmEKoQrhCgAHIQsAB0MLAAcABwAHAAeDC6ABoAHDCwMMAAcABwAHAAdDDGMMAAcAB6MM4wwjDWMNow3jDaABoAGgAaABoAGgAaABoAGgAaABoAGgAaABoAGgAaABoAGgAaABoAEjDqABWw6bDqABpg6gAaABoAHcDvwOPA+gAaABfA/8DvwO/A78DvwO/A78DvwO/A78DvwO/A78DvwO/A78DvwO/A78DvwO/A78DvwO/A78DvwO/A78DpcPAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcAB9cPKwkyCToJMAB1AHUAdQBCCUoJTQl1AFUJXAljCWcJawkwADAAMAAwAHMJdQB2CX4JdQCECYoJjgmWCXUAngkwAGAAYABxAHUApgn3A64JtAl1ALkJdQDACTAAMAAwADAAdQB1AHUAdQB1AHUAdQB1AHUAowYNBMUIMAAwADAAMADICcsJ0wnZCRUE4QkwAOkJ8An4CTAAMAB1AAAKvwh1AAgKDwoXCh8KdQAwACcKLgp1ADYKqAmICT4KRgowADAAdQB1AE4KMAB1AFYKdQBeCnUAZQowADAAMAAwADAAMAAwADAAMAAVBHUAbQowADAAdQC5CXUKMAAwAHwBxAijBogEMgF9CoQKiASMCpQKmgqIBKIKqgquCogEDQG2Cr4KxgrLCjAAMADTCtsKCgHjCusK8Qr5CgELMAAwADAAMAB1AIsECQsRC3UANAEZCzAAMAAwADAAMAB1ACELKQswAHUANAExCzkLdQBBC0kLMABRC1kLMAAwADAAMAAwADAAdQBhCzAAMAAwAGAAYABpC3ELdwt/CzAAMACHC4sLkwubC58Lpwt1AK4Ltgt1APsDMAAwADAAMAAwADAAMAAwAL4LwwvLC9IL1wvdCzAAMADlC+kL8Qv5C/8LSQswADAAMAAwADAAMAAwADAAMAAHDDAAMAAwADAAMAAODBYMHgx1AHUAdQB1AHUAdQB1AHUAdQB1AHUAdQB1AHUAdQB1AHUAdQB1AHUAdQB1AHUAdQB1AHUAdQB1ACYMMAAwADAAdQB1AHUALgx1AHUAdQB1AHUAdQA2DDAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwAHUAdQB1AHUAdQB1AHUAdQB1AHUAdQB1AHUAdQB1AHUAdQB1AD4MdQBGDHUAdQB1AHUAdQB1AEkMdQB1AHUAdQB1AFAMMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwAHUAdQB1AHUAdQB1AHUAdQB1AHUAdQB1AHUAdQBYDHUAdQB1AF8MMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAB1AHUAdQB1AHUAdQB1AHUAdQB1AHUAdQB1AHUAdQB1AHUA+wMVBGcMMAAwAHwBbwx1AHcMfwyHDI8MMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAYABgAJcMMAAwADAAdQB1AJ8MlQClDDAAMACtDCwHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsB7UMLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHdQB1AHUAdQB1AHUAdQB1AHUAdQB1AHUAdQB1AA0EMAC9DDAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAsBywHLAcsBywHLAcsBywHLQcwAMEMyAwsBywHLAcsBywHLAcsBywHLAcsBywHzAwwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwAHUAdQB1ANQM2QzhDDAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMABgAGAAYABgAGAAYABgAOkMYADxDGAA+AwADQYNYABhCWAAYAAODTAAMAAwADAAFg1gAGAAHg37AzAAMAAwADAAYABgACYNYAAsDTQNPA1gAEMNPg1LDWAAYABgAGAAYABgAGAAYABgAGAAUg1aDYsGVglhDV0NcQBnDW0NdQ15DWAAYABgAGAAYABgAGAAYABgAGAAYABgAGAAYABgAGAAlQCBDZUAiA2PDZcNMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAnw2nDTAAMAAwADAAMAAwAHUArw23DTAAMAAwADAAMAAwADAAMAAwADAAMAB1AL8NMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAB1AHUAdQB1AHUAdQDHDTAAYABgAM8NMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAA1w11ANwNMAAwAD0B5A0wADAAMAAwADAAMADsDfQN/A0EDgwOFA4wABsOMAAwADAAMAAwADAAMAAwANIG0gbSBtIG0gbSBtIG0gYjDigOwQUuDsEFMw7SBjoO0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIGQg5KDlIOVg7SBtIGXg5lDm0OdQ7SBtIGfQ6EDooOjQ6UDtIGmg6hDtIG0gaoDqwO0ga0DrwO0gZgAGAAYADEDmAAYAAkBtIGzA5gANIOYADaDokO0gbSBt8O5w7SBu8O0gb1DvwO0gZgAGAAxA7SBtIG0gbSBtIGYABgAGAAYAAED2AAsAUMD9IG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIGFA8sBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAccD9IGLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHJA8sBywHLAcsBywHLAccDywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywPLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAc0D9IG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIGLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAccD9IG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIGFA8sBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHLAcsBywHPA/SBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gbSBtIG0gYUD0QPlQCVAJUAMAAwADAAMACVAJUAlQCVAJUAlQCVAEwPMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAA//8EAAQABAAEAAQABAAEAAQABAANAAMAAQABAAIABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQACgATABcAHgAbABoAHgAXABYAEgAeABsAGAAPABgAHABLAEsASwBLAEsASwBLAEsASwBLABgAGAAeAB4AHgATAB4AUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQABYAGwASAB4AHgAeAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAAWAA0AEQAeAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArAAQABAAEAAQABAAFAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAJABYAGgAbABsAGwAeAB0AHQAeAE8AFwAeAA0AHgAeABoAGwBPAE8ADgBQAB0AHQAdAE8ATwAXAE8ATwBPABYAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAB0AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAdAFAAUABQAFAAUABQAFAAUAAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAFAAHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAAeAB4AHgAeAFAATwBAAE8ATwBPAEAATwBQAFAATwBQAB4AHgAeAB4AHgAeAB0AHQAdAB0AHgAdAB4ADgBQAFAAUABQAFAAHgAeAB4AHgAeAB4AHgBQAB4AUAAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4ABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAJAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAkACQAJAAkACQAJAAkABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAeAB4AHgAeAFAAHgAeAB4AKwArAFAAUABQAFAAGABQACsAKwArACsAHgAeAFAAHgBQAFAAUAArAFAAKwAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AKwAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4ABAAEAAQABAAEAAQABAAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAArACsAUAAeAB4AHgAeAB4AHgBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAAYAA0AKwArAB4AHgAbACsABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQADQAEAB4ABAAEAB4ABAAEABMABAArACsAKwArACsAKwArACsAVgBWAFYAVgBWAFYAVgBWAFYAVgBWAFYAVgBWAFYAVgBWAFYAVgBWAFYAVgBWAFYAVgBWAFYAKwArACsAKwBWAFYAVgBWAB4AHgArACsAKwArACsAKwArACsAKwArACsAHgAeAB4AHgAeAB4AHgAeAB4AGgAaABoAGAAYAB4AHgAEAAQABAAEAAQABAAEAAQABAAEAAQAEwAEACsAEwATAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABABLAEsASwBLAEsASwBLAEsASwBLABoAGQAZAB4AUABQAAQAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQABMAUAAEAAQABAAEAAQABAAEAB4AHgAEAAQABAAEAAQABABQAFAABAAEAB4ABAAEAAQABABQAFAASwBLAEsASwBLAEsASwBLAEsASwBQAFAAUAAeAB4AUAAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AKwAeAFAABABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEACsAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAABAAEAAQABAAEAAQABAAEAAQABAAEAFAAKwArACsAKwArACsAKwArACsAKwArACsAKwArAEsASwBLAEsASwBLAEsASwBLAEsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAABAAEAAQABAAEAAQABAAEAAQAUABQAB4AHgAYABMAUAArACsABAAbABsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAAEAAQABAAEAFAABAAEAAQABAAEAFAABAAEAAQAUAAEAAQABAAEAAQAKwArAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeACsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAAEAAQABAArACsAHgArAFAAUABQAFAAUABQAFAAUABQAFAAUAArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAArAFAAUABQAFAAUABQAFAAUABQAFAAKwArACsAKwArACsAKwArACsAKwArAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAB4ABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAAQABAAEAFAABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQAUAAEAAQABAAEAAQABAAEAFAAUABQAFAAUABQAFAAUABQAFAABAAEAA0ADQBLAEsASwBLAEsASwBLAEsASwBLAB4AUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAAEAAQABAArAFAAUABQAFAAUABQAFAAUAArACsAUABQACsAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAKwBQAFAAUABQAFAAUABQACsAUAArACsAKwBQAFAAUABQACsAKwAEAFAABAAEAAQABAAEAAQABAArACsABAAEACsAKwAEAAQABABQACsAKwArACsAKwArACsAKwAEACsAKwArACsAUABQACsAUABQAFAABAAEACsAKwBLAEsASwBLAEsASwBLAEsASwBLAFAAUAAaABoAUABQAFAAUABQAEwAHgAbAFAAHgAEACsAKwAEAAQABAArAFAAUABQAFAAUABQACsAKwArACsAUABQACsAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAKwBQAFAAUABQAFAAUABQACsAUABQACsAUABQACsAUABQACsAKwAEACsABAAEAAQABAAEACsAKwArACsABAAEACsAKwAEAAQABAArACsAKwAEACsAKwArACsAKwArACsAUABQAFAAUAArAFAAKwArACsAKwArACsAKwBLAEsASwBLAEsASwBLAEsASwBLAAQABABQAFAAUAAEAB4AKwArACsAKwArACsAKwArACsAKwAEAAQABAArAFAAUABQAFAAUABQAFAAUABQACsAUABQAFAAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAKwBQAFAAUABQAFAAUABQACsAUABQACsAUABQAFAAUABQACsAKwAEAFAABAAEAAQABAAEAAQABAAEACsABAAEAAQAKwAEAAQABAArACsAUAArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwBQAFAABAAEACsAKwBLAEsASwBLAEsASwBLAEsASwBLAB4AGwArACsAKwArACsAKwArAFAABAAEAAQABAAEAAQAKwAEAAQABAArAFAAUABQAFAAUABQAFAAUAArACsAUABQACsAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAAQABAAEAAQABAArACsABAAEACsAKwAEAAQABAArACsAKwArACsAKwArAAQABAAEACsAKwArACsAUABQACsAUABQAFAABAAEACsAKwBLAEsASwBLAEsASwBLAEsASwBLAB4AUABQAFAAUABQAFAAUAArACsAKwArACsAKwArACsAKwArAAQAUAArAFAAUABQAFAAUABQACsAKwArAFAAUABQACsAUABQAFAAUAArACsAKwBQAFAAKwBQACsAUABQACsAKwArAFAAUAArACsAKwBQAFAAUAArACsAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUAArACsAKwArAAQABAAEAAQABAArACsAKwAEAAQABAArAAQABAAEAAQAKwArAFAAKwArACsAKwArACsABAArACsAKwArACsAKwArACsAKwArAEsASwBLAEsASwBLAEsASwBLAEsAUABQAFAAHgAeAB4AHgAeAB4AGwAeACsAKwArACsAKwAEAAQABAAEAAQAUABQAFAAUABQAFAAUABQACsAUABQAFAAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAKwArACsAUAAEAAQABAAEAAQABAAEACsABAAEAAQAKwAEAAQABAAEACsAKwArACsAKwArACsABAAEACsAUABQAFAAKwArACsAKwArAFAAUAAEAAQAKwArAEsASwBLAEsASwBLAEsASwBLAEsAKwArACsAKwArACsAKwAOAFAAUABQAFAAUABQAFAAHgBQAAQABAAEAA4AUABQAFAAUABQAFAAUABQACsAUABQAFAAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAArAFAAUABQAFAAUABQAFAAUABQAFAAKwBQAFAAUABQAFAAKwArAAQAUAAEAAQABAAEAAQABAAEACsABAAEAAQAKwAEAAQABAAEACsAKwArACsAKwArACsABAAEACsAKwArACsAKwArACsAUAArAFAAUAAEAAQAKwArAEsASwBLAEsASwBLAEsASwBLAEsAKwBQAFAAKwArACsAKwArACsAKwArACsAKwArACsAKwAEAAQABAAEAFAAUABQAFAAUABQAFAAUABQACsAUABQAFAAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAABAAEAFAABAAEAAQABAAEAAQABAArAAQABAAEACsABAAEAAQABABQAB4AKwArACsAKwBQAFAAUAAEAFAAUABQAFAAUABQAFAAUABQAFAABAAEACsAKwBLAEsASwBLAEsASwBLAEsASwBLAFAAUABQAFAAUABQAFAAUABQABoAUABQAFAAUABQAFAAKwAEAAQABAArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQACsAKwArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAArAFAAUABQAFAAUABQAFAAUABQACsAUAArACsAUABQAFAAUABQAFAAUAArACsAKwAEACsAKwArACsABAAEAAQABAAEAAQAKwAEACsABAAEAAQABAAEAAQABAAEACsAKwArACsAKwArAEsASwBLAEsASwBLAEsASwBLAEsAKwArAAQABAAeACsAKwArACsAKwArACsAKwArACsAKwArAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXAAqAFwAXAAqACoAKgAqACoAKgAqACsAKwArACsAGwBcAFwAXABcAFwAXABcACoAKgAqACoAKgAqACoAKgAeAEsASwBLAEsASwBLAEsASwBLAEsADQANACsAKwArACsAKwBcAFwAKwBcACsAXABcAFwAXABcACsAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcACsAXAArAFwAXABcAFwAXABcAFwAXABcAFwAKgBcAFwAKgAqACoAKgAqACoAKgAqACoAXAArACsAXABcAFwAXABcACsAXAArACoAKgAqACoAKgAqACsAKwBLAEsASwBLAEsASwBLAEsASwBLACsAKwBcAFwAXABcAFAADgAOAA4ADgAeAA4ADgAJAA4ADgANAAkAEwATABMAEwATAAkAHgATAB4AHgAeAAQABAAeAB4AHgAeAB4AHgBLAEsASwBLAEsASwBLAEsASwBLAFAAUABQAFAAUABQAFAAUABQAFAADQAEAB4ABAAeAAQAFgARABYAEQAEAAQAUABQAFAAUABQAFAAUABQACsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAKwArACsAKwAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQADQAEAAQABAAEAAQADQAEAAQAUABQAFAAUABQAAQABAAEAAQABAAEAAQABAAEAAQABAArAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAArAA0ADQAeAB4AHgAeAB4AHgAEAB4AHgAeAB4AHgAeACsAHgAeAA4ADgANAA4AHgAeAB4AHgAeAAkACQArACsAKwArACsAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcACoAKgAqACoAKgAqACoAKgAqACoAKgAqACoAKgAqACoAKgAqACoAKgBcAEsASwBLAEsASwBLAEsASwBLAEsADQANAB4AHgAeAB4AXABcAFwAXABcAFwAKgAqACoAKgBcAFwAXABcACoAKgAqAFwAKgAqACoAXABcACoAKgAqACoAKgAqACoAXABcAFwAKgAqACoAKgBcAFwAXABcAFwAXABcAFwAXABcAFwAXABcACoAKgAqACoAKgAqACoAKgAqACoAKgAqAFwAKgBLAEsASwBLAEsASwBLAEsASwBLACoAKgAqACoAKgAqAFAAUABQAFAAUABQACsAUAArACsAKwArACsAUAArACsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAHgBQAFAAUABQAFgAWABYAFgAWABYAFgAWABYAFgAWABYAFgAWABYAFgAWABYAFgAWABYAFgAWABYAFgAWABYAFgAWABYAFgAWABZAFkAWQBZAFkAWQBZAFkAWQBZAFkAWQBZAFkAWQBZAFkAWQBZAFkAWQBZAFkAWQBZAFkAWQBZAFkAWQBZAFkAWgBaAFoAWgBaAFoAWgBaAFoAWgBaAFoAWgBaAFoAWgBaAFoAWgBaAFoAWgBaAFoAWgBaAFoAWgBaAFoAWgBaAFAAUABQAFAAUABQAFAAUABQACsAUABQAFAAUAArACsAUABQAFAAUABQAFAAUAArAFAAKwBQAFAAUABQACsAKwBQAFAAUABQAFAAUABQAFAAUAArAFAAUABQAFAAKwArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAArAFAAUABQAFAAKwArAFAAUABQAFAAUABQAFAAKwBQACsAUABQAFAAUAArACsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAKwBQAFAAUABQACsAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAArACsABAAEAAQAHgANAB4AHgAeAB4AHgAeAB4AUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQACsAKwArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAHgAeAB4AHgAeAB4AHgAeAB4AHgArACsAKwArACsAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQACsAKwBQAFAAUABQAFAAUAArACsADQBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAHgAeAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAANAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAAWABEAKwArACsAUABQAFAAUABQAFAAUABQAFAAUABQAA0ADQANAFAAUABQAFAAUABQAFAAUABQAFAAUAArACsAKwArACsAKwArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAKwBQAFAAUABQAAQABAAEACsAKwArACsAKwArACsAKwArACsAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAAEAAQABAANAA0AKwArACsAKwArACsAKwArACsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAABAAEACsAKwArACsAKwArACsAKwArACsAKwArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAKwBQAFAAUAArAAQABAArACsAKwArACsAKwArACsAKwArACsAKwBcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAKgAqACoAKgAqACoAKgAqACoAKgAqACoAKgAqACoAKgAqACoAKgAqAA0ADQAVAFwADQAeAA0AGwBcACoAKwArAEsASwBLAEsASwBLAEsASwBLAEsAKwArACsAKwArACsAUABQAFAAUABQAFAAUABQAFAAUAArACsAKwArACsAKwAeAB4AEwATAA0ADQAOAB4AEwATAB4ABAAEAAQACQArAEsASwBLAEsASwBLAEsASwBLAEsAKwArACsAKwArACsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAArACsAKwArACsAKwArAFAAUABQAFAAUAAEAAQAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAAQAUAArACsAKwArACsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAArACsAKwArACsAKwArACsAKwArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAKwAEAAQABAAEAAQABAAEAAQABAAEAAQABAArACsAKwArAAQABAAEAAQABAAEAAQABAAEAAQABAAEACsAKwArACsAHgArACsAKwATABMASwBLAEsASwBLAEsASwBLAEsASwBcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXAArACsAXABcAFwAXABcACsAKwArACsAKwArACsAKwArACsAKwBcAFwAXABcAFwAXABcAFwAXABcAFwAXAArACsAKwArAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcACsAKwArACsAKwArAEsASwBLAEsASwBLAEsASwBLAEsAXAArACsAKwAqACoAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAAQABAAEAAQABAArACsAHgAeAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcACoAKgAqACoAKgAqACoAKgAqACoAKwAqACoAKgAqACoAKgAqACoAKgAqACoAKgAqACoAKgAqACoAKgAqACoAKgAqACoAKgAqACoAKgAqACoAKwArAAQASwBLAEsASwBLAEsASwBLAEsASwArACsAKwArACsAKwBLAEsASwBLAEsASwBLAEsASwBLACsAKwArACsAKwArACoAKgAqACoAKgAqACoAXAAqACoAKgAqACoAKgArACsABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsABAAEAAQABAAEAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAAQABAAEAAQABABQAFAAUABQAFAAUABQACsAKwArACsASwBLAEsASwBLAEsASwBLAEsASwANAA0AHgANAA0ADQANAB4AHgAeAB4AHgAeAB4AHgAeAB4ABAAEAAQABAAEAAQABAAEAAQAHgAeAB4AHgAeAB4AHgAeAB4AKwArACsABAAEAAQAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAABAAEAAQABAAEAAQABAAEAAQABAAEAAQABABQAFAASwBLAEsASwBLAEsASwBLAEsASwBQAFAAUABQAFAAUABQAFAABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEACsAKwArACsAKwArACsAKwAeAB4AHgAeAFAAUABQAFAABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEACsAKwArAA0ADQANAA0ADQBLAEsASwBLAEsASwBLAEsASwBLACsAKwArAFAAUABQAEsASwBLAEsASwBLAEsASwBLAEsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAA0ADQBQAFAAUABQAFAAUABQAFAAUAArACsAKwArACsAKwArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQACsAKwBQAFAAUAAeAB4AHgAeAB4AHgAeAB4AKwArACsAKwArACsAKwArAAQABAAEAB4ABAAEAAQABAAEAAQABAAEAAQABAAEAAQABABQAFAAUABQAAQAUABQAFAAUABQAFAABABQAFAABAAEAAQAUAArACsAKwArACsABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEACsABAAEAAQABAAEAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AKwArAFAAUABQAFAAUABQACsAKwBQAFAAUABQAFAAUABQAFAAKwBQACsAUAArAFAAKwAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeACsAKwAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgArAB4AHgAeAB4AHgAeAB4AHgBQAB4AHgAeAFAAUABQACsAHgAeAB4AHgAeAB4AHgAeAB4AHgBQAFAAUABQACsAKwAeAB4AHgAeAB4AHgArAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AKwArAFAAUABQACsAHgAeAB4AHgAeAB4AHgAOAB4AKwANAA0ADQANAA0ADQANAAkADQANAA0ACAAEAAsABAAEAA0ACQANAA0ADAAdAB0AHgAXABcAFgAXABcAFwAWABcAHQAdAB4AHgAUABQAFAANAAEAAQAEAAQABAAEAAQACQAaABoAGgAaABoAGgAaABoAHgAXABcAHQAVABUAHgAeAB4AHgAeAB4AGAAWABEAFQAVABUAHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4ADQAeAA0ADQANAA0AHgANAA0ADQAHAB4AHgAeAB4AKwAEAAQABAAEAAQABAAEAAQABAAEAFAAUAArACsATwBQAFAAUABQAFAAHgAeAB4AFgARAE8AUABPAE8ATwBPAFAAUABQAFAAUAAeAB4AHgAWABEAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQACsAKwArABsAGwAbABsAGwAbABsAGgAbABsAGwAbABsAGwAbABsAGwAbABsAGwAbABsAGgAbABsAGwAbABoAGwAbABoAGwAbABsAGwAbABsAGwAbABsAGwAbABsAGwAbABsAGwAbAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQAHgAeAFAAGgAeAB0AHgBQAB4AGgAeAB4AHgAeAB4AHgAeAB4AHgBPAB4AUAAbAB4AHgBQAFAAUABQAFAAHgAeAB4AHQAdAB4AUAAeAFAAHgBQAB4AUABPAFAAUAAeAB4AHgAeAB4AHgAeAFAAUABQAFAAUAAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAFAAHgBQAFAAUABQAE8ATwBQAFAAUABQAFAATwBQAFAATwBQAE8ATwBPAE8ATwBPAE8ATwBPAE8ATwBPAFAAUABQAFAATwBPAE8ATwBPAE8ATwBPAE8ATwBQAFAAUABQAFAAUABQAFAAUAAeAB4AUABQAFAAUABPAB4AHgArACsAKwArAB0AHQAdAB0AHQAdAB0AHQAdAB0AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB0AHgAdAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAdAB4AHQAdAB4AHgAeAB0AHQAeAB4AHQAeAB4AHgAdAB4AHQAbABsAHgAdAB4AHgAeAB4AHQAeAB4AHQAdAB0AHQAeAB4AHQAeAB0AHgAdAB0AHQAdAB0AHQAeAB0AHgAeAB4AHgAeAB0AHQAdAB0AHgAeAB4AHgAdAB0AHgAeAB4AHgAeAB4AHgAeAB4AHgAdAB4AHgAeAB0AHgAeAB4AHgAeAB0AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAdAB0AHgAeAB0AHQAdAB0AHgAeAB0AHQAeAB4AHQAdAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB0AHQAeAB4AHQAdAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHQAeAB4AHgAdAB4AHgAeAB4AHgAeAB4AHQAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB0AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AFAAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeABYAEQAWABEAHgAeAB4AHgAeAB4AHQAeAB4AHgAeAB4AHgAeACUAJQAeAB4AHgAeAB4AHgAeAB4AHgAWABEAHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AJQAlACUAJQAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArAE8ATwBPAE8ATwBPAE8ATwBPAE8ATwBPAE8ATwBPAE8ATwBPAE8ATwBPAE8ATwBPAE8ATwBPAE8ATwBPAE8ATwAdAB0AHQAdAB0AHQAdAB0AHQAdAB0AHQAdAB0AHQAdAB0AHQAdAB0AHQAdAB0AHQAdAB0AHQAdAB0AHQAdAB0AHQAdAE8ATwBPAE8ATwBPAE8ATwBPAE8ATwBPAE8ATwBPAE8ATwBPAE8ATwBPAFAAHQAdAB0AHQAdAB0AHQAdAB0AHQAdAB0AHgAeAB4AHgAdAB0AHQAdAB0AHQAdAB0AHQAdAB0AHQAdAB0AHQAdAB0AHQAdAB0AHQAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHQAdAB0AHQAdAB0AHQAdAB0AHQAdAB0AHQAdAB0AHQAeAB4AHQAdAB0AHQAeAB4AHgAeAB4AHgAeAB4AHgAeAB0AHQAeAB0AHQAdAB0AHQAdAB0AHgAeAB4AHgAeAB4AHgAeAB0AHQAeAB4AHQAdAB4AHgAeAB4AHQAdAB4AHgAeAB4AHQAdAB0AHgAeAB0AHgAeAB0AHQAdAB0AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAdAB0AHQAdAB4AHgAeAB4AHgAeAB4AHgAeAB0AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAlACUAJQAlAB4AHQAdAB4AHgAdAB4AHgAeAB4AHQAdAB4AHgAeAB4AJQAlAB0AHQAlAB4AJQAlACUAIAAlACUAHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAlACUAJQAeAB4AHgAeAB0AHgAdAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAdAB0AHgAdAB0AHQAeAB0AJQAdAB0AHgAdAB0AHgAdAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeACUAHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHQAdAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAlACUAJQAlACUAJQAlACUAJQAlACUAJQAdAB0AHQAdACUAHgAlACUAJQAdACUAJQAdAB0AHQAlACUAHQAdACUAHQAdACUAJQAlAB4AHQAeAB4AHgAeAB0AHQAlAB0AHQAdAB0AHQAdACUAJQAlACUAJQAdACUAJQAgACUAHQAdACUAJQAlACUAJQAlACUAJQAeAB4AHgAlACUAIAAgACAAIAAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB0AHgAeAB4AFwAXABcAFwAXABcAHgATABMAJQAeAB4AHgAWABEAFgARABYAEQAWABEAFgARABYAEQAWABEATwBPAE8ATwBPAE8ATwBPAE8ATwBPAE8ATwBPAE8ATwBPAE8ATwBPAE8ATwAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeABYAEQAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAWABEAFgARABYAEQAWABEAFgARAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AFgARABYAEQAWABEAFgARABYAEQAWABEAFgARABYAEQAWABEAFgARABYAEQAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAWABEAFgARAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AFgARAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAdAB0AHQAdAB0AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgArACsAHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AKwAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AUABQAFAAUAAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAEAAQABAAeAB4AKwArACsAKwArABMADQANAA0AUAATAA0AUABQAFAAUABQAFAAUABQACsAKwArACsAKwArACsAUAANACsAKwArACsAKwArACsAKwArACsAKwArACsAKwAEAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAArACsAKwArACsAKwArACsAKwBQAFAAUABQAFAAUABQACsAUABQAFAAUABQAFAAUAArAFAAUABQAFAAUABQAFAAKwBQAFAAUABQAFAAUABQACsAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXAA0ADQANAA0ADQANAA0ADQAeAA0AFgANAB4AHgAXABcAHgAeABcAFwAWABEAFgARABYAEQAWABEADQANAA0ADQATAFAADQANAB4ADQANAB4AHgAeAB4AHgAMAAwADQANAA0AHgANAA0AFgANAA0ADQANAA0ADQANAA0AHgANAB4ADQANAB4AHgAeACsAKwArACsAKwArACsAKwArACsAKwArACsAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACsAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAKwArACsAKwArACsAKwArACsAKwArACsAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwAlACUAJQAlACUAJQAlACUAJQAlACUAJQArACsAKwArAA0AEQARACUAJQBHAFcAVwAWABEAFgARABYAEQAWABEAFgARACUAJQAWABEAFgARABYAEQAWABEAFQAWABEAEQAlAFcAVwBXAFcAVwBXAFcAVwBXAAQABAAEAAQABAAEACUAVwBXAFcAVwA2ACUAJQBXAFcAVwBHAEcAJQAlACUAKwBRAFcAUQBXAFEAVwBRAFcAUQBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFEAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBRAFcAUQBXAFEAVwBXAFcAVwBXAFcAUQBXAFcAVwBXAFcAVwBRAFEAKwArAAQABAAVABUARwBHAFcAFQBRAFcAUQBXAFEAVwBRAFcAUQBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFEAVwBRAFcAUQBXAFcAVwBXAFcAVwBRAFcAVwBXAFcAVwBXAFEAUQBXAFcAVwBXABUAUQBHAEcAVwArACsAKwArACsAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAKwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAKwAlACUAVwBXAFcAVwAlACUAJQAlACUAJQAlACUAJQAlACsAKwArACsAKwArACsAKwArACsAKwArAFEAUQBRAFEAUQBRAFEAUQBRAFEAUQBRAFEAUQBRAFEAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQArAFcAVwBXAFcAVwBXAFcAVwBXAFcAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQBPAE8ATwBPAE8ATwBPAE8AJQBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXACUAJQAlAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAEcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAKwArACsAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQArACsAKwArACsAKwArACsAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAADQATAA0AUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABLAEsASwBLAEsASwBLAEsASwBLAFAAUAArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAFAABAAEAAQABAAeAAQABAAEAAQABAAEAAQABAAEAAQAHgBQAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AUABQAAQABABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAAQABAAeAA0ADQANAA0ADQArACsAKwArACsAKwArACsAHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAFAAUABQAFAAUABQAFAAUABQAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AUAAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgBQAB4AHgAeAB4AHgAeAFAAHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgArACsAHgAeAB4AHgAeAB4AHgAeAB4AKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwAeAB4AUABQAFAAUABQAFAAUABQAFAAUABQAAQAUABQAFAABABQAFAAUABQAAQAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAAQABAAEAAQABAAeAB4AHgAeAAQAKwArACsAUABQAFAAUABQAFAAHgAeABoAHgArACsAKwArACsAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAADgAOABMAEwArACsAKwArACsAKwArACsABAAEAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAAQABAAEAAQABAAEACsAKwArACsAKwArACsAKwANAA0ASwBLAEsASwBLAEsASwBLAEsASwArACsAKwArACsAKwAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABABQAFAAUABQAFAAUAAeAB4AHgBQAA4AUABQAAQAUABQAFAAUABQAFAABAAEAAQABAAEAAQABAAEAA0ADQBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQAKwArACsAKwArACsAKwArACsAKwArAB4AWABYAFgAWABYAFgAWABYAFgAWABYAFgAWABYAFgAWABYAFgAWABYAFgAWABYAFgAWABYAFgAWABYACsAKwArAAQAHgAeAB4AHgAeAB4ADQANAA0AHgAeAB4AHgArAFAASwBLAEsASwBLAEsASwBLAEsASwArACsAKwArAB4AHgBcAFwAXABcAFwAKgBcAFwAXABcAFwAXABcAFwAXABcAEsASwBLAEsASwBLAEsASwBLAEsAXABcAFwAXABcACsAUABQAFAAUABQAFAAUABQAFAABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEACsAKwArACsAKwArACsAKwArAFAAUABQAAQAUABQAFAAUABQAFAAUABQAAQABAArACsASwBLAEsASwBLAEsASwBLAEsASwArACsAHgANAA0ADQBcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAKgAqACoAXAAqACoAKgBcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXAAqAFwAKgAqACoAXABcACoAKgBcAFwAXABcAFwAKgAqAFwAKgBcACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArAFwAXABcACoAKgBQAFAAUABQAFAAUABQAFAAUABQAFAABAAEAAQABAAEAA0ADQBQAFAAUAAEAAQAKwArACsAKwArACsAKwArACsAKwBQAFAAUABQAFAAUAArACsAUABQAFAAUABQAFAAKwArAFAAUABQAFAAUABQACsAKwArACsAKwArACsAKwArAFAAUABQAFAAUABQAFAAKwBQAFAAUABQAFAAUABQACsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAHgAeACsAKwArACsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAAEAAQABAAEAAQABAAEAAQADQAEAAQAKwArAEsASwBLAEsASwBLAEsASwBLAEsAKwArACsAKwArACsAVABVAFUAVQBVAFUAVQBVAFUAVQBVAFUAVQBVAFUAVQBVAFUAVQBVAFUAVQBVAFUAVQBVAFUAVQBUAFUAVQBVAFUAVQBVAFUAVQBVAFUAVQBVAFUAVQBVAFUAVQBVAFUAVQBVAFUAVQBVAFUAVQBVACsAKwArACsAKwArACsAKwArACsAKwArAFkAWQBZAFkAWQBZAFkAWQBZAFkAWQBZAFkAWQBZAFkAWQBZAFkAKwArACsAKwBaAFoAWgBaAFoAWgBaAFoAWgBaAFoAWgBaAFoAWgBaAFoAWgBaAFoAWgBaAFoAWgBaAFoAWgBaAFoAKwArACsAKwAGAAYABgAGAAYABgAGAAYABgAGAAYABgAGAAYABgAGAAYABgAGAAYABgAGAAYABgAGAAYABgAGAAYABgAGAAYAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXACUAJQBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAJQAlACUAJQAlACUAUABQAFAAUABQAFAAUAArACsAKwArACsAKwArACsAKwArACsAKwBQAFAAUABQAFAAKwArACsAKwArAFYABABWAFYAVgBWAFYAVgBWAFYAVgBWAB4AVgBWAFYAVgBWAFYAVgBWAFYAVgBWAFYAVgArAFYAVgBWAFYAVgArAFYAKwBWAFYAKwBWAFYAKwBWAFYAVgBWAFYAVgBWAFYAVgBWAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAEQAWAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAKwArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUAAaAB4AKwArAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQAGAARABEAGAAYABMAEwAWABEAFAArACsAKwArACsAKwAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEACUAJQAlACUAJQAWABEAFgARABYAEQAWABEAFgARABYAEQAlACUAFgARACUAJQAlACUAJQAlACUAEQAlABEAKwAVABUAEwATACUAFgARABYAEQAWABEAJQAlACUAJQAlACUAJQAlACsAJQAbABoAJQArACsAKwArAFAAUABQAFAAUAArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAKwArAAcAKwATACUAJQAbABoAJQAlABYAEQAlACUAEQAlABEAJQBXAFcAVwBXAFcAVwBXAFcAVwBXABUAFQAlACUAJQATACUAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXABYAJQARACUAJQAlAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwAWACUAEQAlABYAEQARABYAEQARABUAVwBRAFEAUQBRAFEAUQBRAFEAUQBRAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAEcARwArACsAVwBXAFcAVwBXAFcAKwArAFcAVwBXAFcAVwBXACsAKwBXAFcAVwBXAFcAVwArACsAVwBXAFcAKwArACsAGgAbACUAJQAlABsAGwArAB4AHgAeAB4AHgAeAB4AKwArACsAKwArACsAKwArACsAKwAEAAQABAAQAB0AKwArAFAAUABQAFAAUABQAFAAUABQAFAAUABQACsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAKwBQAFAAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAArACsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQACsAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAArACsAKwArACsADQANAA0AKwArACsAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQACsAKwArAB4AHgAeAB4AHgAeAB4AHgAeAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgBQAFAAHgAeAB4AKwAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAAQAKwArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwAEAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQACsAKwArACsAKwArACsAKwArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAKwArACsAKwArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAABAAEAAQABAAEACsAKwArACsAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAArAA0AUABQAFAAUAArACsAKwArAFAAUABQAFAAUABQAFAAUAANAFAAUABQAFAAUAArACsAKwArACsAKwArACsAKwArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQACsAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAKwArACsAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQACsAKwArACsAKwArACsAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQACsAKwArACsAKwArACsAKwArACsAKwAeACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAUABQAFAAUABQAFAAKwArAFAAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAArAFAAUAArACsAKwBQACsAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAKwANAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAAeAB4AUABQAFAAUABQAFAAUAArACsAKwArACsAKwArAFAAUABQAFAAUABQAFAAUABQACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAArAFAAUAArACsAKwArACsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQACsAKwArAA0AUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQACsAKwArACsAKwAeAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQACsAKwArACsAUABQAFAAUABQAAQABAAEACsABAAEACsAKwArACsAKwAEAAQABAAEAFAAUABQAFAAKwBQAFAAUAArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAKwArAAQABAAEACsAKwArACsABABQAFAAUABQAFAAUABQAFAAUAArACsAKwArACsAKwArAA0ADQANAA0ADQANAA0ADQAeACsAKwArACsAKwArACsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAAeAFAAUABQAFAAUABQAFAAUAAeAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAAQABAArACsAKwArAFAAUABQAFAAUAANAA0ADQANAA0ADQAUACsAKwArACsAKwArACsAKwArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAKwArACsADQANAA0ADQANAA0ADQBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAArACsAKwArACsAKwArAB4AHgAeAB4AKwArACsAKwArACsAKwArACsAKwArACsAUABQAFAAUABQAFAAUAArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArAFAAUABQAFAAUABQAFAAUABQACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQACsAKwArACsAKwArACsAKwArACsAKwArACsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAArACsAKwArACsAKwArAFAAUABQAFAAUABQAAQABAAEAAQAKwArACsAKwArACsAKwArAEsASwBLAEsASwBLAEsASwBLAEsAKwArACsAKwArACsAUABQAFAAUABQAFAAUABQAFAAUAArAAQABAANACsAKwBQAFAAKwArACsAKwArACsAKwArACsAKwArACsAKwArAFAAUABQAFAAUABQAAQABAAEAAQABAAEAAQABAAEAAQABABQAFAAUABQAB4AHgAeAB4AHgArACsAKwArACsAKwAEAAQABAAEAAQABAAEAA0ADQAeAB4AHgAeAB4AKwArACsAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAEsASwBLAEsASwBLAEsASwBLAEsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsABABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAAQABAAEAAQABAAEAAQABAAEAAQABAAeAB4AHgANAA0ADQANACsAKwArACsAKwArACsAKwArACsAKwAeACsAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAKwArACsAKwArACsAKwBLAEsASwBLAEsASwBLAEsASwBLACsAKwArACsAKwArAFAAUABQAFAAUABQAFAABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEACsASwBLAEsASwBLAEsASwBLAEsASwANAA0ADQANAFAABAAEAFAAKwArACsAKwArACsAKwArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAABAAeAA4AUAArACsAKwArACsAKwArACsAKwAEAFAAUABQAFAADQANAB4ADQAEAAQABAAEAB4ABAAEAEsASwBLAEsASwBLAEsASwBLAEsAUAAOAFAADQANAA0AKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAKwArACsAKwArACsAKwArACsAKwArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQACsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAAEAAQABAAEAAQABAAEAAQABAAEAAQABAANAA0AHgANAA0AHgAEACsAUABQAFAAUABQAFAAUAArAFAAKwBQAFAAUABQACsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAKwBQAFAAUABQAFAAUABQAFAAUABQAA0AKwArACsAKwArACsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAAEAAQABAAEAAQABAAEAAQABAAEAAQAKwArACsAKwArAEsASwBLAEsASwBLAEsASwBLAEsAKwArACsAKwArACsABAAEAAQABAArAFAAUABQAFAAUABQAFAAUAArACsAUABQACsAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAKwBQAFAAUABQAFAAUABQACsAUABQACsAUABQAFAAUABQACsABAAEAFAABAAEAAQABAAEAAQABAArACsABAAEACsAKwAEAAQABAArACsAUAArACsAKwArACsAKwAEACsAKwArACsAKwBQAFAAUABQAFAABAAEACsAKwAEAAQABAAEAAQABAAEACsAKwArAAQABAAEAAQABAArACsAKwArACsAKwArACsAKwArACsABAAEAAQABAAEAAQABABQAFAAUABQAA0ADQANAA0AHgBLAEsASwBLAEsASwBLAEsASwBLAA0ADQArAB4ABABQAFAAUAArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwAEAAQABAAEAFAAUAAeAFAAKwArACsAKwArACsAKwArAEsASwBLAEsASwBLAEsASwBLAEsAKwArACsAKwArACsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAABAAEAAQABAAEAAQABAArACsABAAEAAQABAAEAAQABAAEAAQADgANAA0AEwATAB4AHgAeAA0ADQANAA0ADQANAA0ADQANAA0ADQANAA0ADQANAFAAUABQAFAABAAEACsAKwAEAA0ADQAeAFAAKwArACsAKwArACsAKwArACsAKwArAEsASwBLAEsASwBLAEsASwBLAEsAKwArACsAKwArACsADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArAFAAUABQAFAAUABQAFAAUABQAFAAUAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAFAAKwArACsAKwArACsAKwBLAEsASwBLAEsASwBLAEsASwBLACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAXABcAFwAKwArACoAKgAqACoAKgAqACoAKgAqACoAKgAqACoAKgAqACsAKwArACsASwBLAEsASwBLAEsASwBLAEsASwBcAFwADQANAA0AKgBQAFAAUABQAFAAUABQAFAAUABQAFAAUAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAeACsAKwArACsASwBLAEsASwBLAEsASwBLAEsASwBQAFAAUABQAFAAUABQAFAAUAArACsAKwArACsAKwArACsAKwArACsAKwBQAFAAUABQAFAAUABQAFAAKwArAFAAKwArAFAAUABQAFAAUABQAFAAUAArAFAAUAArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAABAAEAAQABAAEAAQAKwAEAAQAKwArAAQABAAEAAQAUAAEAFAABAAEAA0ADQANACsAKwArACsAKwArACsAKwArAEsASwBLAEsASwBLAEsASwBLAEsAKwArACsAKwArACsAUABQAFAAUABQAFAAUABQACsAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAABAAEAAQABAAEAAQABAArACsABAAEAAQABAAEAAQABABQAA4AUAAEACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArAFAABAAEAAQABAAEAAQABAAEAAQABABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAAEAAQABAAEAAQABAAEAFAABAAEAAQABAAOAB4ADQANAA0ADQAOAB4ABAArACsAKwArACsAKwArACsAUAAEAAQABAAEAAQABAAEAAQABAAEAAQAUABQAFAAUABQAFAAUABQAFAAUAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAA0ADQANAFAADgAOAA4ADQANACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwBQAFAAUABQAFAAUABQAFAAUAArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAABAAEAAQABAAEAAQABAAEACsABAAEAAQABAAEAAQABAAEAFAADQANAA0ADQANACsAKwArACsAKwArACsAKwArACsASwBLAEsASwBLAEsASwBLAEsASwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAArACsAKwAOABMAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAKwArAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAArAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAArACsAKwArACsAKwArACsAKwBQAFAAUABQAFAAUABQACsAUABQACsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAAEAAQABAAEAAQABAArACsAKwAEACsABAAEACsABAAEAAQABAAEAAQABABQAAQAKwArACsAKwArACsAKwArAEsASwBLAEsASwBLAEsASwBLAEsAKwArACsAKwArACsAUABQAFAAUABQAFAAKwBQAFAAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAAEAAQABAAEAAQAKwAEAAQAKwAEAAQABAAEAAQAUAArACsAKwArACsAKwArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAABAAEAAQABAAeAB4AKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwBQACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAB4AHgAeAB4AHgAeAB4AHgAaABoAGgAaAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgArACsAKwArACsAKwArACsAKwArACsAKwArAA0AUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQACsAKwArACsAKwArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQACsADQANAA0ADQANACsAKwArACsAKwArACsAKwArACsAKwBQAFAAUABQACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAASABIAEgAQwBDAEMAUABQAFAAUABDAFAAUABQAEgAQwBIAEMAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAASABDAEMAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAKwAJAAkACQAJAAkACQAJABYAEQArACsAKwArACsAKwArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABIAEMAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArAEsASwBLAEsASwBLAEsASwBLAEsAKwArACsAKwANAA0AKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAKwArAAQABAAEAAQABAANACsAKwArACsAKwArACsAKwArACsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAAEAAQABAAEAAQABAAEAA0ADQANAB4AHgAeAB4AHgAeAFAAUABQAFAADQAeACsAKwArACsAKwArACsAKwArACsASwBLAEsASwBLAEsASwBLAEsASwArAFAAUABQAFAAUABQAFAAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAArACsAKwArACsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAANAA0AHgAeACsAKwArACsAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAKwArACsAKwAEAFAABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQAKwArACsAKwArACsAKwAEAAQABAAEAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAARwBHABUARwAJACsAKwArACsAKwArACsAKwArACsAKwAEAAQAKwArACsAKwArACsAKwArACsAKwArACsAKwArAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXACsAKwArACsAKwArACsAKwBXAFcAVwBXAFcAVwBXAFcAVwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAUQBRAFEAKwArACsAKwArACsAKwArACsAKwArACsAKwBRAFEAUQBRACsAKwArACsAKwArACsAKwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXACsAKwArACsAUABQAFAAUABQAFAAUABQAFAAUABQACsAKwArACsAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQACsAKwArACsAKwArACsAUABQAFAAUABQAFAAUABQAFAAUAArACsAHgAEAAQADQAEAAQABAAEACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgArACsAKwArACsAKwArACsAKwArAB4AHgAeAB4AHgAeAB4AKwArAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAAQABAAEAAQABAAeAB4AHgAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAB4AHgAEAAQABAAEAAQABAAEAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4ABAAEAAQABAAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4ABAAEAAQAHgArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQACsAKwArACsAKwArACsAKwArACsAKwArAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgArACsAKwArACsAKwArACsAKwAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgArAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AKwBQAFAAKwArAFAAKwArAFAAUAArACsAUABQAFAAUAArAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeACsAUAArAFAAUABQAFAAUABQAFAAKwAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AKwBQAFAAUABQACsAKwBQAFAAUABQAFAAUABQAFAAKwBQAFAAUABQAFAAUABQACsAHgAeAFAAUABQAFAAUAArAFAAKwArACsAUABQAFAAUABQAFAAUAArAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AKwArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAHgBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgBQAFAAUABQAFAAUABQAFAAUABQAFAAHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAB4AHgAeAB4AHgAeAB4AHgAeACsAKwBLAEsASwBLAEsASwBLAEsASwBLAEsASwBLAEsASwBLAEsASwBLAEsASwBLAEsASwBLAEsASwBLAEsASwBLAEsASwBLAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAeAB4AHgAeAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAeAB4AHgAeAB4AHgAeAB4ABAAeAB4AHgAeAB4AHgAeAB4AHgAeAAQAHgAeAA0ADQANAA0AHgArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwAEAAQABAAEAAQAKwAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArAAQABAAEAAQABAAEAAQAKwAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQAKwArAAQABAAEAAQABAAEAAQAKwAEAAQAKwAEAAQABAAEAAQAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAArACsAKwAEAAQABAAEAAQABAAEAFAAUABQAFAAUABQAFAAKwArAEsASwBLAEsASwBLAEsASwBLAEsAKwArACsAKwBQAB4AKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUAAEAAQABAAEAEsASwBLAEsASwBLAEsASwBLAEsAKwArACsAKwArABsAUABQAFAAUABQACsAKwBQAFAAUABQAFAAUABQAFAAUAAEAAQABAAEAAQABAAEACsAKwArACsAKwArACsAKwArAB4AHgAeAB4ABAAEAAQABAAEAAQABABQACsAKwArACsASwBLAEsASwBLAEsASwBLAEsASwArACsAKwArABYAFgArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAGgBQAFAAUAAaAFAAUABQAFAAKwArACsAKwArACsAKwArACsAKwArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAAeAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQACsAKwBQAFAAUABQACsAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAKwBQAFAAKwBQACsAKwBQACsAUABQAFAAUABQAFAAUABQAFAAUAArAFAAUABQAFAAKwBQACsAUAArACsAKwArACsAKwBQACsAKwArACsAUAArAFAAKwBQACsAUABQAFAAKwBQAFAAKwBQACsAKwBQACsAUAArAFAAKwBQACsAUAArAFAAUAArAFAAKwArAFAAUABQAFAAKwBQAFAAUABQAFAAUABQACsAUABQAFAAUAArAFAAUABQAFAAKwBQACsAUABQAFAAUABQAFAAUABQAFAAUAArAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAArACsAKwArACsAUABQAFAAKwBQAFAAUABQAFAAKwBQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwAeAB4AKwArACsAKwArACsAKwArACsAKwArACsAKwArAE8ATwBPAE8ATwBPAE8ATwBPAE8ATwBPAE8AJQAlACUAHQAdAB0AHQAdAB0AHQAdAB0AHQAdAB0AHQAdAB0AHQAdAB0AHgAeAB0AHQAdAB0AHQAdAB0AHQAdAB0AHQAdAB0AHQAdAB0AHQAdAB4AHgAeACUAJQAlAB0AHQAdAB0AHQAdAB0AHQAdAB0AHQAdAB0AHQAdAB0AHQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQApACkAKQApACkAKQApACkAKQApACkAKQApACkAKQApACkAKQApACkAKQApACkAKQApACkAJQAlACUAJQAlACAAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAeAB4AJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlAB4AHgAlACUAJQAlACUAHgAlACUAJQAlACUAIAAgACAAJQAlACAAJQAlACAAIAAgACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACEAIQAhACEAIQAlACUAIAAgACUAJQAgACAAIAAgACAAIAAgACAAIAAgACAAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAJQAlACUAIAAlACUAJQAlACAAIAAgACUAIAAgACAAJQAlACUAJQAlACUAJQAgACUAIAAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAHgAlAB4AJQAeACUAJQAlACUAJQAgACUAJQAlACUAHgAlAB4AHgAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlAB4AHgAeAB4AHgAeAB4AJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAeAB4AHgAeAB4AHgAeAB4AHgAeACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACAAIAAlACUAJQAlACAAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACAAJQAlACUAJQAgACAAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAHgAeAB4AHgAeAB4AHgAeACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAeAB4AHgAeAB4AHgAlACUAJQAlACUAJQAlACAAIAAgACUAJQAlACAAIAAgACAAIAAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeABcAFwAXABUAFQAVAB4AHgAeAB4AJQAlACUAIAAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACAAIAAgACUAJQAlACUAJQAlACUAJQAlACAAJQAlACUAJQAlACUAJQAlACUAJQAlACAAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AJQAlACUAJQAlACUAJQAlACUAJQAlACUAHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AJQAlACUAJQAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeACUAJQAlACUAJQAlACUAJQAeAB4AHgAeAB4AHgAeAB4AHgAeACUAJQAlACUAJQAlAB4AHgAeAB4AHgAeAB4AHgAlACUAJQAlACUAJQAlACUAHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAgACUAJQAgACUAJQAlACUAJQAlACUAJQAgACAAIAAgACAAIAAgACAAJQAlACUAJQAlACUAIAAlACUAJQAlACUAJQAlACUAJQAgACAAIAAgACAAIAAgACAAIAAgACUAJQAgACAAIAAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAgACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACAAIAAlACAAIAAlACAAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAgACAAIAAlACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAJQAlAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AKwAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArAEsASwBLAEsASwBLAEsASwBLAEsAKwArACsAKwArACsAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAKwArAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXACUAJQBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwAlACUAJQAlACUAJQAlACUAJQAlACUAVwBXACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQBXAFcAVwBXAFcAVwBXAFcAVwBXAFcAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAJQAlACUAKwAEACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArAA==",
    Kr = 50,
    wB = 1,
    Dn = 2,
    Sn = 3,
    fB = 4,
    CB = 5,
    br = 7,
    Tn = 8,
    xr = 9,
    EA = 10,
    Xt = 11,
    Dr = 12,
    Jt = 13,
    hB = 14,
    Be = 15,
    Yt = 16,
    Le = 17,
    ee = 18,
    UB = 19,
    Sr = 20,
    Wt = 21,
    te = 22,
    Ht = 23,
    VA = 24,
    z = 25,
    ie = 26,
    ae = 27,
    kA = 28,
    FB = 29,
    OA = 30,
    dB = 31,
    Ke = 32,
    be = 33,
    Zt = 34,
    qt = 35,
    jt = 36,
    Ce = 37,
    zt = 38,
    Ze = 39,
    qe = 40,
    vt = 41,
    On = 42,
    pB = 43,
    EB = [9001, 65288],
    Mn = "!",
    I = "×",
    xe = "÷",
    $t = lB(QB),
    uA = [OA, jt],
    Ar = [wB, Dn, Sn, CB],
    Rn = [EA, Tn],
    Tr = [ae, ie],
    HB = Ar.concat(Rn),
    Or = [zt, Ze, qe, Zt, qt],
    vB = [Be, Jt],
    IB = function (t, A) {
        A === void 0 && (A = "strict");
        var e = [],
            r = [],
            n = [];
        return (
            t.forEach(function (s, B) {
                var i = $t.get(s);
                if (
                    (i > Kr ? (n.push(!0), (i -= Kr)) : n.push(!1),
                    ["normal", "auto", "loose"].indexOf(A) !== -1 && [8208, 8211, 12316, 12448].indexOf(s) !== -1)
                )
                    return r.push(B), e.push(Yt);
                if (i === fB || i === Xt) {
                    if (B === 0) return r.push(B), e.push(OA);
                    var a = e[B - 1];
                    return HB.indexOf(a) === -1 ? (r.push(r[B - 1]), e.push(a)) : (r.push(B), e.push(OA));
                }
                if ((r.push(B), i === dB)) return e.push(A === "strict" ? Wt : Ce);
                if (i === On || i === FB) return e.push(OA);
                if (i === pB)
                    return (s >= 131072 && s <= 196605) || (s >= 196608 && s <= 262141) ? e.push(Ce) : e.push(OA);
                e.push(i);
            }),
            [r, e, n]
        );
    },
    It = function (t, A, e, r) {
        var n = r[e];
        if (Array.isArray(t) ? t.indexOf(n) !== -1 : t === n)
            for (var s = e; s <= r.length; ) {
                s++;
                var B = r[s];
                if (B === A) return !0;
                if (B !== EA) break;
            }
        if (n === EA)
            for (var s = e; s > 0; ) {
                s--;
                var i = r[s];
                if (Array.isArray(t) ? t.indexOf(i) !== -1 : t === i)
                    for (var a = e; a <= r.length; ) {
                        a++;
                        var B = r[a];
                        if (B === A) return !0;
                        if (B !== EA) break;
                    }
                if (i !== EA) break;
            }
        return !1;
    },
    Mr = function (t, A) {
        for (var e = t; e >= 0; ) {
            var r = A[e];
            if (r === EA) e--;
            else return r;
        }
        return 0;
    },
    mB = function (t, A, e, r, n) {
        if (e[r] === 0) return I;
        var s = r - 1;
        if (Array.isArray(n) && n[s] === !0) return I;
        var B = s - 1,
            i = s + 1,
            a = A[s],
            o = B >= 0 ? A[B] : 0,
            c = A[i];
        if (a === Dn && c === Sn) return I;
        if (Ar.indexOf(a) !== -1) return Mn;
        if (Ar.indexOf(c) !== -1 || Rn.indexOf(c) !== -1) return I;
        if (Mr(s, A) === Tn) return xe;
        if (
            $t.get(t[s]) === Xt ||
            ((a === Ke || a === be) && $t.get(t[i]) === Xt) ||
            a === br ||
            c === br ||
            a === xr ||
            ([EA, Jt, Be].indexOf(a) === -1 && c === xr) ||
            [Le, ee, UB, VA, kA].indexOf(c) !== -1 ||
            Mr(s, A) === te ||
            It(Ht, te, s, A) ||
            It([Le, ee], Wt, s, A) ||
            It(Dr, Dr, s, A)
        )
            return I;
        if (a === EA) return xe;
        if (a === Ht || c === Ht) return I;
        if (c === Yt || a === Yt) return xe;
        if (
            [Jt, Be, Wt].indexOf(c) !== -1 ||
            a === hB ||
            (o === jt && vB.indexOf(a) !== -1) ||
            (a === kA && c === jt) ||
            c === Sr ||
            (uA.indexOf(c) !== -1 && a === z) ||
            (uA.indexOf(a) !== -1 && c === z) ||
            (a === ae && [Ce, Ke, be].indexOf(c) !== -1) ||
            ([Ce, Ke, be].indexOf(a) !== -1 && c === ie) ||
            (uA.indexOf(a) !== -1 && Tr.indexOf(c) !== -1) ||
            (Tr.indexOf(a) !== -1 && uA.indexOf(c) !== -1) ||
            ([ae, ie].indexOf(a) !== -1 && (c === z || ([te, Be].indexOf(c) !== -1 && A[i + 1] === z))) ||
            ([te, Be].indexOf(a) !== -1 && c === z) ||
            (a === z && [z, kA, VA].indexOf(c) !== -1)
        )
            return I;
        if ([z, kA, VA, Le, ee].indexOf(c) !== -1)
            for (var l = s; l >= 0; ) {
                var g = A[l];
                if (g === z) return I;
                if ([kA, VA].indexOf(g) !== -1) l--;
                else break;
            }
        if ([ae, ie].indexOf(c) !== -1)
            for (var l = [Le, ee].indexOf(a) !== -1 ? B : s; l >= 0; ) {
                var g = A[l];
                if (g === z) return I;
                if ([kA, VA].indexOf(g) !== -1) l--;
                else break;
            }
        if (
            (zt === a && [zt, Ze, Zt, qt].indexOf(c) !== -1) ||
            ([Ze, Zt].indexOf(a) !== -1 && [Ze, qe].indexOf(c) !== -1) ||
            ([qe, qt].indexOf(a) !== -1 && c === qe) ||
            (Or.indexOf(a) !== -1 && [Sr, ie].indexOf(c) !== -1) ||
            (Or.indexOf(c) !== -1 && a === ae) ||
            (uA.indexOf(a) !== -1 && uA.indexOf(c) !== -1) ||
            (a === VA && uA.indexOf(c) !== -1) ||
            (uA.concat(z).indexOf(a) !== -1 && c === te && EB.indexOf(t[i]) === -1) ||
            (uA.concat(z).indexOf(c) !== -1 && a === ee)
        )
            return I;
        if (a === vt && c === vt) {
            for (var w = e[s], Q = 1; w > 0 && (w--, A[w] === vt); ) Q++;
            if (Q % 2 !== 0) return I;
        }
        return a === Ke && c === be ? I : xe;
    },
    yB = function (t, A) {
        A || (A = { lineBreak: "normal", wordBreak: "normal" });
        var e = IB(t, A.lineBreak),
            r = e[0],
            n = e[1],
            s = e[2];
        (A.wordBreak === "break-all" || A.wordBreak === "break-word") &&
            (n = n.map(function (i) {
                return [z, OA, On].indexOf(i) !== -1 ? Ce : i;
            }));
        var B =
            A.wordBreak === "keep-all"
                ? s.map(function (i, a) {
                      return i && t[a] >= 19968 && t[a] <= 40959;
                  })
                : void 0;
        return [r, n, B];
    },
    LB = (function () {
        function t(A, e, r, n) {
            (this.codePoints = A), (this.required = e === Mn), (this.start = r), (this.end = n);
        }
        return (
            (t.prototype.slice = function () {
                return O.apply(void 0, this.codePoints.slice(this.start, this.end));
            }),
            t
        );
    })(),
    KB = function (t, A) {
        var e = gt(t),
            r = yB(e, A),
            n = r[0],
            s = r[1],
            B = r[2],
            i = e.length,
            a = 0,
            o = 0;
        return {
            next: function () {
                if (o >= i) return { done: !0, value: null };
                for (var c = I; o < i && (c = mB(e, s, n, ++o, B)) === I; );
                if (c !== I || o === i) {
                    var l = new LB(e, c, a, o);
                    return (a = o), { value: l, done: !1 };
                }
                return { done: !0, value: null };
            },
        };
    },
    bB = 1 << 0,
    xB = 1 << 1,
    Fe = 1 << 2,
    Rr = 1 << 3,
    At = 10,
    Nr = 47,
    ge = 92,
    DB = 9,
    SB = 32,
    De = 34,
    re = 61,
    TB = 35,
    OB = 36,
    MB = 37,
    Se = 39,
    Te = 40,
    ne = 41,
    RB = 95,
    q = 45,
    NB = 33,
    GB = 60,
    VB = 62,
    kB = 64,
    PB = 91,
    _B = 93,
    XB = 61,
    JB = 123,
    Oe = 63,
    YB = 125,
    Gr = 124,
    WB = 126,
    ZB = 128,
    Vr = 65533,
    mt = 42,
    MA = 43,
    qB = 44,
    jB = 58,
    zB = 59,
    he = 46,
    $B = 0,
    Ai = 8,
    ei = 11,
    ti = 14,
    ri = 31,
    ni = 127,
    iA = -1,
    Nn = 48,
    Gn = 97,
    Vn = 101,
    si = 102,
    Bi = 117,
    ii = 122,
    kn = 65,
    Pn = 69,
    _n = 70,
    ai = 85,
    oi = 90,
    X = function (t) {
        return t >= Nn && t <= 57;
    },
    ci = function (t) {
        return t >= 55296 && t <= 57343;
    },
    PA = function (t) {
        return X(t) || (t >= kn && t <= _n) || (t >= Gn && t <= si);
    },
    li = function (t) {
        return t >= Gn && t <= ii;
    },
    gi = function (t) {
        return t >= kn && t <= oi;
    },
    ui = function (t) {
        return li(t) || gi(t);
    },
    Qi = function (t) {
        return t >= ZB;
    },
    Me = function (t) {
        return t === At || t === DB || t === SB;
    },
    et = function (t) {
        return ui(t) || Qi(t) || t === RB;
    },
    kr = function (t) {
        return et(t) || X(t) || t === q;
    },
    wi = function (t) {
        return (t >= $B && t <= Ai) || t === ei || (t >= ti && t <= ri) || t === ni;
    },
    pA = function (t, A) {
        return t !== ge ? !1 : A !== At;
    },
    Re = function (t, A, e) {
        return t === q ? et(A) || pA(A, e) : et(t) ? !0 : !!(t === ge && pA(t, A));
    },
    yt = function (t, A, e) {
        return t === MA || t === q ? (X(A) ? !0 : A === he && X(e)) : X(t === he ? A : t);
    },
    fi = function (t) {
        var A = 0,
            e = 1;
        (t[A] === MA || t[A] === q) && (t[A] === q && (e = -1), A++);
        for (var r = []; X(t[A]); ) r.push(t[A++]);
        var n = r.length ? parseInt(O.apply(void 0, r), 10) : 0;
        t[A] === he && A++;
        for (var s = []; X(t[A]); ) s.push(t[A++]);
        var B = s.length,
            i = B ? parseInt(O.apply(void 0, s), 10) : 0;
        (t[A] === Pn || t[A] === Vn) && A++;
        var a = 1;
        (t[A] === MA || t[A] === q) && (t[A] === q && (a = -1), A++);
        for (var o = []; X(t[A]); ) o.push(t[A++]);
        var c = o.length ? parseInt(O.apply(void 0, o), 10) : 0;
        return e * (n + i * Math.pow(10, -B)) * Math.pow(10, a * c);
    },
    Ci = { type: 2 },
    hi = { type: 3 },
    Ui = { type: 4 },
    Fi = { type: 13 },
    di = { type: 8 },
    pi = { type: 21 },
    Ei = { type: 9 },
    Hi = { type: 10 },
    vi = { type: 11 },
    Ii = { type: 12 },
    mi = { type: 14 },
    Ne = { type: 23 },
    yi = { type: 1 },
    Li = { type: 25 },
    Ki = { type: 24 },
    bi = { type: 26 },
    xi = { type: 27 },
    Di = { type: 28 },
    Si = { type: 29 },
    Ti = { type: 31 },
    er = { type: 32 },
    Xn = (function () {
        function t() {
            this._value = [];
        }
        return (
            (t.prototype.write = function (A) {
                this._value = this._value.concat(gt(A));
            }),
            (t.prototype.read = function () {
                for (var A = [], e = this.consumeToken(); e !== er; ) A.push(e), (e = this.consumeToken());
                return A;
            }),
            (t.prototype.consumeToken = function () {
                var A = this.consumeCodePoint();
                switch (A) {
                    case De:
                        return this.consumeStringToken(De);
                    case TB:
                        var e = this.peekCodePoint(0),
                            r = this.peekCodePoint(1),
                            n = this.peekCodePoint(2);
                        if (kr(e) || pA(r, n)) {
                            var s = Re(e, r, n) ? xB : bB,
                                B = this.consumeName();
                            return { type: 5, value: B, flags: s };
                        }
                        break;
                    case OB:
                        if (this.peekCodePoint(0) === re) return this.consumeCodePoint(), Fi;
                        break;
                    case Se:
                        return this.consumeStringToken(Se);
                    case Te:
                        return Ci;
                    case ne:
                        return hi;
                    case mt:
                        if (this.peekCodePoint(0) === re) return this.consumeCodePoint(), mi;
                        break;
                    case MA:
                        if (yt(A, this.peekCodePoint(0), this.peekCodePoint(1)))
                            return this.reconsumeCodePoint(A), this.consumeNumericToken();
                        break;
                    case qB:
                        return Ui;
                    case q:
                        var i = A,
                            a = this.peekCodePoint(0),
                            o = this.peekCodePoint(1);
                        if (yt(i, a, o)) return this.reconsumeCodePoint(A), this.consumeNumericToken();
                        if (Re(i, a, o)) return this.reconsumeCodePoint(A), this.consumeIdentLikeToken();
                        if (a === q && o === VB) return this.consumeCodePoint(), this.consumeCodePoint(), Ki;
                        break;
                    case he:
                        if (yt(A, this.peekCodePoint(0), this.peekCodePoint(1)))
                            return this.reconsumeCodePoint(A), this.consumeNumericToken();
                        break;
                    case Nr:
                        if (this.peekCodePoint(0) === mt)
                            for (this.consumeCodePoint(); ; ) {
                                var c = this.consumeCodePoint();
                                if (c === mt && ((c = this.consumeCodePoint()), c === Nr)) return this.consumeToken();
                                if (c === iA) return this.consumeToken();
                            }
                        break;
                    case jB:
                        return bi;
                    case zB:
                        return xi;
                    case GB:
                        if (this.peekCodePoint(0) === NB && this.peekCodePoint(1) === q && this.peekCodePoint(2) === q)
                            return this.consumeCodePoint(), this.consumeCodePoint(), Li;
                        break;
                    case kB:
                        var l = this.peekCodePoint(0),
                            g = this.peekCodePoint(1),
                            w = this.peekCodePoint(2);
                        if (Re(l, g, w)) {
                            var B = this.consumeName();
                            return { type: 7, value: B };
                        }
                        break;
                    case PB:
                        return Di;
                    case ge:
                        if (pA(A, this.peekCodePoint(0)))
                            return this.reconsumeCodePoint(A), this.consumeIdentLikeToken();
                        break;
                    case _B:
                        return Si;
                    case XB:
                        if (this.peekCodePoint(0) === re) return this.consumeCodePoint(), di;
                        break;
                    case JB:
                        return vi;
                    case YB:
                        return Ii;
                    case Bi:
                    case ai:
                        var Q = this.peekCodePoint(0),
                            f = this.peekCodePoint(1);
                        return (
                            Q === MA &&
                                (PA(f) || f === Oe) &&
                                (this.consumeCodePoint(), this.consumeUnicodeRangeToken()),
                            this.reconsumeCodePoint(A),
                            this.consumeIdentLikeToken()
                        );
                    case Gr:
                        if (this.peekCodePoint(0) === re) return this.consumeCodePoint(), Ei;
                        if (this.peekCodePoint(0) === Gr) return this.consumeCodePoint(), pi;
                        break;
                    case WB:
                        if (this.peekCodePoint(0) === re) return this.consumeCodePoint(), Hi;
                        break;
                    case iA:
                        return er;
                }
                return Me(A)
                    ? (this.consumeWhiteSpace(), Ti)
                    : X(A)
                    ? (this.reconsumeCodePoint(A), this.consumeNumericToken())
                    : et(A)
                    ? (this.reconsumeCodePoint(A), this.consumeIdentLikeToken())
                    : { type: 6, value: O(A) };
            }),
            (t.prototype.consumeCodePoint = function () {
                var A = this._value.shift();
                return typeof A == "undefined" ? -1 : A;
            }),
            (t.prototype.reconsumeCodePoint = function (A) {
                this._value.unshift(A);
            }),
            (t.prototype.peekCodePoint = function (A) {
                return A >= this._value.length ? -1 : this._value[A];
            }),
            (t.prototype.consumeUnicodeRangeToken = function () {
                for (var A = [], e = this.consumeCodePoint(); PA(e) && A.length < 6; )
                    A.push(e), (e = this.consumeCodePoint());
                for (var r = !1; e === Oe && A.length < 6; ) A.push(e), (e = this.consumeCodePoint()), (r = !0);
                if (r) {
                    var n = parseInt(
                            O.apply(
                                void 0,
                                A.map(function (a) {
                                    return a === Oe ? Nn : a;
                                })
                            ),
                            16
                        ),
                        s = parseInt(
                            O.apply(
                                void 0,
                                A.map(function (a) {
                                    return a === Oe ? _n : a;
                                })
                            ),
                            16
                        );
                    return { type: 30, start: n, end: s };
                }
                var B = parseInt(O.apply(void 0, A), 16);
                if (this.peekCodePoint(0) === q && PA(this.peekCodePoint(1))) {
                    this.consumeCodePoint(), (e = this.consumeCodePoint());
                    for (var i = []; PA(e) && i.length < 6; ) i.push(e), (e = this.consumeCodePoint());
                    var s = parseInt(O.apply(void 0, i), 16);
                    return { type: 30, start: B, end: s };
                } else return { type: 30, start: B, end: B };
            }),
            (t.prototype.consumeIdentLikeToken = function () {
                var A = this.consumeName();
                return A.toLowerCase() === "url" && this.peekCodePoint(0) === Te
                    ? (this.consumeCodePoint(), this.consumeUrlToken())
                    : this.peekCodePoint(0) === Te
                    ? (this.consumeCodePoint(), { type: 19, value: A })
                    : { type: 20, value: A };
            }),
            (t.prototype.consumeUrlToken = function () {
                var A = [];
                if ((this.consumeWhiteSpace(), this.peekCodePoint(0) === iA)) return { type: 22, value: "" };
                var e = this.peekCodePoint(0);
                if (e === Se || e === De) {
                    var r = this.consumeStringToken(this.consumeCodePoint());
                    return r.type === 0 &&
                        (this.consumeWhiteSpace(), this.peekCodePoint(0) === iA || this.peekCodePoint(0) === ne)
                        ? (this.consumeCodePoint(), { type: 22, value: r.value })
                        : (this.consumeBadUrlRemnants(), Ne);
                }
                for (;;) {
                    var n = this.consumeCodePoint();
                    if (n === iA || n === ne) return { type: 22, value: O.apply(void 0, A) };
                    if (Me(n))
                        return (
                            this.consumeWhiteSpace(),
                            this.peekCodePoint(0) === iA || this.peekCodePoint(0) === ne
                                ? (this.consumeCodePoint(), { type: 22, value: O.apply(void 0, A) })
                                : (this.consumeBadUrlRemnants(), Ne)
                        );
                    if (n === De || n === Se || n === Te || wi(n)) return this.consumeBadUrlRemnants(), Ne;
                    if (n === ge)
                        if (pA(n, this.peekCodePoint(0))) A.push(this.consumeEscapedCodePoint());
                        else return this.consumeBadUrlRemnants(), Ne;
                    else A.push(n);
                }
            }),
            (t.prototype.consumeWhiteSpace = function () {
                for (; Me(this.peekCodePoint(0)); ) this.consumeCodePoint();
            }),
            (t.prototype.consumeBadUrlRemnants = function () {
                for (;;) {
                    var A = this.consumeCodePoint();
                    if (A === ne || A === iA) return;
                    pA(A, this.peekCodePoint(0)) && this.consumeEscapedCodePoint();
                }
            }),
            (t.prototype.consumeStringSlice = function (A) {
                for (var e = 5e4, r = ""; A > 0; ) {
                    var n = Math.min(e, A);
                    (r += O.apply(void 0, this._value.splice(0, n))), (A -= n);
                }
                return this._value.shift(), r;
            }),
            (t.prototype.consumeStringToken = function (A) {
                var e = "",
                    r = 0;
                do {
                    var n = this._value[r];
                    if (n === iA || n === void 0 || n === A)
                        return (e += this.consumeStringSlice(r)), { type: 0, value: e };
                    if (n === At) return this._value.splice(0, r), yi;
                    if (n === ge) {
                        var s = this._value[r + 1];
                        s !== iA &&
                            s !== void 0 &&
                            (s === At
                                ? ((e += this.consumeStringSlice(r)), (r = -1), this._value.shift())
                                : pA(n, s) &&
                                  ((e += this.consumeStringSlice(r)),
                                  (e += O(this.consumeEscapedCodePoint())),
                                  (r = -1)));
                    }
                    r++;
                } while (!0);
            }),
            (t.prototype.consumeNumber = function () {
                var A = [],
                    e = Fe,
                    r = this.peekCodePoint(0);
                for ((r === MA || r === q) && A.push(this.consumeCodePoint()); X(this.peekCodePoint(0)); )
                    A.push(this.consumeCodePoint());
                r = this.peekCodePoint(0);
                var n = this.peekCodePoint(1);
                if (r === he && X(n))
                    for (A.push(this.consumeCodePoint(), this.consumeCodePoint()), e = Rr; X(this.peekCodePoint(0)); )
                        A.push(this.consumeCodePoint());
                (r = this.peekCodePoint(0)), (n = this.peekCodePoint(1));
                var s = this.peekCodePoint(2);
                if ((r === Pn || r === Vn) && (((n === MA || n === q) && X(s)) || X(n)))
                    for (A.push(this.consumeCodePoint(), this.consumeCodePoint()), e = Rr; X(this.peekCodePoint(0)); )
                        A.push(this.consumeCodePoint());
                return [fi(A), e];
            }),
            (t.prototype.consumeNumericToken = function () {
                var A = this.consumeNumber(),
                    e = A[0],
                    r = A[1],
                    n = this.peekCodePoint(0),
                    s = this.peekCodePoint(1),
                    B = this.peekCodePoint(2);
                if (Re(n, s, B)) {
                    var i = this.consumeName();
                    return { type: 15, number: e, flags: r, unit: i };
                }
                return n === MB
                    ? (this.consumeCodePoint(), { type: 16, number: e, flags: r })
                    : { type: 17, number: e, flags: r };
            }),
            (t.prototype.consumeEscapedCodePoint = function () {
                var A = this.consumeCodePoint();
                if (PA(A)) {
                    for (var e = O(A); PA(this.peekCodePoint(0)) && e.length < 6; ) e += O(this.consumeCodePoint());
                    Me(this.peekCodePoint(0)) && this.consumeCodePoint();
                    var r = parseInt(e, 16);
                    return r === 0 || ci(r) || r > 1114111 ? Vr : r;
                }
                return A === iA ? Vr : A;
            }),
            (t.prototype.consumeName = function () {
                for (var A = ""; ; ) {
                    var e = this.consumeCodePoint();
                    if (kr(e)) A += O(e);
                    else if (pA(e, this.peekCodePoint(0))) A += O(this.consumeEscapedCodePoint());
                    else return this.reconsumeCodePoint(e), A;
                }
            }),
            t
        );
    })(),
    Jn = (function () {
        function t(A) {
            this._tokens = A;
        }
        return (
            (t.create = function (A) {
                var e = new Xn();
                return e.write(A), new t(e.read());
            }),
            (t.parseValue = function (A) {
                return t.create(A).parseComponentValue();
            }),
            (t.parseValues = function (A) {
                return t.create(A).parseComponentValues();
            }),
            (t.prototype.parseComponentValue = function () {
                for (var A = this.consumeToken(); A.type === 31; ) A = this.consumeToken();
                if (A.type === 32) throw new SyntaxError("Error parsing CSS component value, unexpected EOF");
                this.reconsumeToken(A);
                var e = this.consumeComponentValue();
                do A = this.consumeToken();
                while (A.type === 31);
                if (A.type === 32) return e;
                throw new SyntaxError(
                    "Error parsing CSS component value, multiple values found when expecting only one"
                );
            }),
            (t.prototype.parseComponentValues = function () {
                for (var A = []; ; ) {
                    var e = this.consumeComponentValue();
                    if (e.type === 32) return A;
                    A.push(e), A.push();
                }
            }),
            (t.prototype.consumeComponentValue = function () {
                var A = this.consumeToken();
                switch (A.type) {
                    case 11:
                    case 28:
                    case 2:
                        return this.consumeSimpleBlock(A.type);
                    case 19:
                        return this.consumeFunction(A);
                }
                return A;
            }),
            (t.prototype.consumeSimpleBlock = function (A) {
                for (var e = { type: A, values: [] }, r = this.consumeToken(); ; ) {
                    if (r.type === 32 || Mi(r, A)) return e;
                    this.reconsumeToken(r), e.values.push(this.consumeComponentValue()), (r = this.consumeToken());
                }
            }),
            (t.prototype.consumeFunction = function (A) {
                for (var e = { name: A.value, values: [], type: 18 }; ; ) {
                    var r = this.consumeToken();
                    if (r.type === 32 || r.type === 3) return e;
                    this.reconsumeToken(r), e.values.push(this.consumeComponentValue());
                }
            }),
            (t.prototype.consumeToken = function () {
                var A = this._tokens.shift();
                return typeof A == "undefined" ? er : A;
            }),
            (t.prototype.reconsumeToken = function (A) {
                this._tokens.unshift(A);
            }),
            t
        );
    })(),
    de = function (t) {
        return t.type === 15;
    },
    zA = function (t) {
        return t.type === 17;
    },
    x = function (t) {
        return t.type === 20;
    },
    Oi = function (t) {
        return t.type === 0;
    },
    tr = function (t, A) {
        return x(t) && t.value === A;
    },
    Yn = function (t) {
        return t.type !== 31;
    },
    jA = function (t) {
        return t.type !== 31 && t.type !== 4;
    },
    oA = function (t) {
        var A = [],
            e = [];
        return (
            t.forEach(function (r) {
                if (r.type === 4) {
                    if (e.length === 0) throw new Error("Error parsing function args, zero tokens for arg");
                    A.push(e), (e = []);
                    return;
                }
                r.type !== 31 && e.push(r);
            }),
            e.length && A.push(e),
            A
        );
    },
    Mi = function (t, A) {
        return (A === 11 && t.type === 12) || (A === 28 && t.type === 29) ? !0 : A === 2 && t.type === 3;
    },
    yA = function (t) {
        return t.type === 17 || t.type === 15;
    },
    R = function (t) {
        return t.type === 16 || yA(t);
    },
    Wn = function (t) {
        return t.length > 1 ? [t[0], t[1]] : [t[0]];
    },
    P = { type: 17, number: 0, flags: Fe },
    wr = { type: 16, number: 50, flags: Fe },
    HA = { type: 16, number: 100, flags: Fe },
    oe = function (t, A, e) {
        var r = t[0],
            n = t[1];
        return [D(r, A), D(typeof n != "undefined" ? n : r, e)];
    },
    D = function (t, A) {
        if (t.type === 16) return (t.number / 100) * A;
        if (de(t))
            switch (t.unit) {
                case "rem":
                case "em":
                    return 16 * t.number;
                case "px":
                default:
                    return t.number;
            }
        return t.number;
    },
    Zn = "deg",
    qn = "grad",
    jn = "rad",
    zn = "turn",
    ut = {
        name: "angle",
        parse: function (t, A) {
            if (A.type === 15)
                switch (A.unit) {
                    case Zn:
                        return (Math.PI * A.number) / 180;
                    case qn:
                        return (Math.PI / 200) * A.number;
                    case jn:
                        return A.number;
                    case zn:
                        return Math.PI * 2 * A.number;
                }
            throw new Error("Unsupported angle type");
        },
    },
    $n = function (t) {
        return t.type === 15 && (t.unit === Zn || t.unit === qn || t.unit === jn || t.unit === zn);
    },
    As = function (t) {
        var A = t
            .filter(x)
            .map(function (e) {
                return e.value;
            })
            .join(" ");
        switch (A) {
            case "to bottom right":
            case "to right bottom":
            case "left top":
            case "top left":
                return [P, P];
            case "to top":
            case "bottom":
                return tA(0);
            case "to bottom left":
            case "to left bottom":
            case "right top":
            case "top right":
                return [P, HA];
            case "to right":
            case "left":
                return tA(90);
            case "to top left":
            case "to left top":
            case "right bottom":
            case "bottom right":
                return [HA, HA];
            case "to bottom":
            case "top":
                return tA(180);
            case "to top right":
            case "to right top":
            case "left bottom":
            case "bottom left":
                return [HA, P];
            case "to left":
            case "right":
                return tA(270);
        }
        return 0;
    },
    tA = function (t) {
        return (Math.PI * t) / 180;
    },
    IA = {
        name: "color",
        parse: function (t, A) {
            if (A.type === 18) {
                var e = Ri[A.name];
                if (typeof e == "undefined")
                    throw new Error('Attempting to parse an unsupported color function "' + A.name + '"');
                return e(t, A.values);
            }
            if (A.type === 5) {
                if (A.value.length === 3) {
                    var r = A.value.substring(0, 1),
                        n = A.value.substring(1, 2),
                        s = A.value.substring(2, 3);
                    return vA(parseInt(r + r, 16), parseInt(n + n, 16), parseInt(s + s, 16), 1);
                }
                if (A.value.length === 4) {
                    var r = A.value.substring(0, 1),
                        n = A.value.substring(1, 2),
                        s = A.value.substring(2, 3),
                        B = A.value.substring(3, 4);
                    return vA(parseInt(r + r, 16), parseInt(n + n, 16), parseInt(s + s, 16), parseInt(B + B, 16) / 255);
                }
                if (A.value.length === 6) {
                    var r = A.value.substring(0, 2),
                        n = A.value.substring(2, 4),
                        s = A.value.substring(4, 6);
                    return vA(parseInt(r, 16), parseInt(n, 16), parseInt(s, 16), 1);
                }
                if (A.value.length === 8) {
                    var r = A.value.substring(0, 2),
                        n = A.value.substring(2, 4),
                        s = A.value.substring(4, 6),
                        B = A.value.substring(6, 8);
                    return vA(parseInt(r, 16), parseInt(n, 16), parseInt(s, 16), parseInt(B, 16) / 255);
                }
            }
            if (A.type === 20) {
                var i = wA[A.value.toUpperCase()];
                if (typeof i != "undefined") return i;
            }
            return wA.TRANSPARENT;
        },
    },
    mA = function (t) {
        return (255 & t) === 0;
    },
    G = function (t) {
        var A = 255 & t,
            e = 255 & (t >> 8),
            r = 255 & (t >> 16),
            n = 255 & (t >> 24);
        return A < 255 ? "rgba(" + n + "," + r + "," + e + "," + A / 255 + ")" : "rgb(" + n + "," + r + "," + e + ")";
    },
    vA = function (t, A, e, r) {
        return ((t << 24) | (A << 16) | (e << 8) | (Math.round(r * 255) << 0)) >>> 0;
    },
    Pr = function (t, A) {
        if (t.type === 17) return t.number;
        if (t.type === 16) {
            var e = A === 3 ? 1 : 255;
            return A === 3 ? (t.number / 100) * e : Math.round((t.number / 100) * e);
        }
        return 0;
    },
    _r = function (t, A) {
        var e = A.filter(jA);
        if (e.length === 3) {
            var r = e.map(Pr),
                n = r[0],
                s = r[1],
                B = r[2];
            return vA(n, s, B, 1);
        }
        if (e.length === 4) {
            var i = e.map(Pr),
                n = i[0],
                s = i[1],
                B = i[2],
                a = i[3];
            return vA(n, s, B, a);
        }
        return 0;
    };
function Lt(t, A, e) {
    return (
        e < 0 && (e += 1),
        e >= 1 && (e -= 1),
        e < 1 / 6 ? (A - t) * e * 6 + t : e < 1 / 2 ? A : e < 2 / 3 ? (A - t) * 6 * (2 / 3 - e) + t : t
    );
}
var Xr = function (t, A) {
        var e = A.filter(jA),
            r = e[0],
            n = e[1],
            s = e[2],
            B = e[3],
            i = (r.type === 17 ? tA(r.number) : ut.parse(t, r)) / (Math.PI * 2),
            a = R(n) ? n.number / 100 : 0,
            o = R(s) ? s.number / 100 : 0,
            c = typeof B != "undefined" && R(B) ? D(B, 1) : 1;
        if (a === 0) return vA(o * 255, o * 255, o * 255, 1);
        var l = o <= 0.5 ? o * (a + 1) : o + a - o * a,
            g = o * 2 - l,
            w = Lt(g, l, i + 1 / 3),
            Q = Lt(g, l, i),
            f = Lt(g, l, i - 1 / 3);
        return vA(w * 255, Q * 255, f * 255, c);
    },
    Ri = { hsl: Xr, hsla: Xr, rgb: _r, rgba: _r },
    ue = function (t, A) {
        return IA.parse(t, Jn.create(A).parseComponentValue());
    },
    wA = {
        ALICEBLUE: 4042850303,
        ANTIQUEWHITE: 4209760255,
        AQUA: 16777215,
        AQUAMARINE: 2147472639,
        AZURE: 4043309055,
        BEIGE: 4126530815,
        BISQUE: 4293182719,
        BLACK: 255,
        BLANCHEDALMOND: 4293643775,
        BLUE: 65535,
        BLUEVIOLET: 2318131967,
        BROWN: 2771004159,
        BURLYWOOD: 3736635391,
        CADETBLUE: 1604231423,
        CHARTREUSE: 2147418367,
        CHOCOLATE: 3530104575,
        CORAL: 4286533887,
        CORNFLOWERBLUE: 1687547391,
        CORNSILK: 4294499583,
        CRIMSON: 3692313855,
        CYAN: 16777215,
        DARKBLUE: 35839,
        DARKCYAN: 9145343,
        DARKGOLDENROD: 3095837695,
        DARKGRAY: 2846468607,
        DARKGREEN: 6553855,
        DARKGREY: 2846468607,
        DARKKHAKI: 3182914559,
        DARKMAGENTA: 2332068863,
        DARKOLIVEGREEN: 1433087999,
        DARKORANGE: 4287365375,
        DARKORCHID: 2570243327,
        DARKRED: 2332033279,
        DARKSALMON: 3918953215,
        DARKSEAGREEN: 2411499519,
        DARKSLATEBLUE: 1211993087,
        DARKSLATEGRAY: 793726975,
        DARKSLATEGREY: 793726975,
        DARKTURQUOISE: 13554175,
        DARKVIOLET: 2483082239,
        DEEPPINK: 4279538687,
        DEEPSKYBLUE: 12582911,
        DIMGRAY: 1768516095,
        DIMGREY: 1768516095,
        DODGERBLUE: 512819199,
        FIREBRICK: 2988581631,
        FLORALWHITE: 4294635775,
        FORESTGREEN: 579543807,
        FUCHSIA: 4278255615,
        GAINSBORO: 3705462015,
        GHOSTWHITE: 4177068031,
        GOLD: 4292280575,
        GOLDENROD: 3668254975,
        GRAY: 2155905279,
        GREEN: 8388863,
        GREENYELLOW: 2919182335,
        GREY: 2155905279,
        HONEYDEW: 4043305215,
        HOTPINK: 4285117695,
        INDIANRED: 3445382399,
        INDIGO: 1258324735,
        IVORY: 4294963455,
        KHAKI: 4041641215,
        LAVENDER: 3873897215,
        LAVENDERBLUSH: 4293981695,
        LAWNGREEN: 2096890111,
        LEMONCHIFFON: 4294626815,
        LIGHTBLUE: 2916673279,
        LIGHTCORAL: 4034953471,
        LIGHTCYAN: 3774873599,
        LIGHTGOLDENRODYELLOW: 4210742015,
        LIGHTGRAY: 3553874943,
        LIGHTGREEN: 2431553791,
        LIGHTGREY: 3553874943,
        LIGHTPINK: 4290167295,
        LIGHTSALMON: 4288707327,
        LIGHTSEAGREEN: 548580095,
        LIGHTSKYBLUE: 2278488831,
        LIGHTSLATEGRAY: 2005441023,
        LIGHTSLATEGREY: 2005441023,
        LIGHTSTEELBLUE: 2965692159,
        LIGHTYELLOW: 4294959359,
        LIME: 16711935,
        LIMEGREEN: 852308735,
        LINEN: 4210091775,
        MAGENTA: 4278255615,
        MAROON: 2147483903,
        MEDIUMAQUAMARINE: 1724754687,
        MEDIUMBLUE: 52735,
        MEDIUMORCHID: 3126187007,
        MEDIUMPURPLE: 2473647103,
        MEDIUMSEAGREEN: 1018393087,
        MEDIUMSLATEBLUE: 2070474495,
        MEDIUMSPRINGGREEN: 16423679,
        MEDIUMTURQUOISE: 1221709055,
        MEDIUMVIOLETRED: 3340076543,
        MIDNIGHTBLUE: 421097727,
        MINTCREAM: 4127193855,
        MISTYROSE: 4293190143,
        MOCCASIN: 4293178879,
        NAVAJOWHITE: 4292783615,
        NAVY: 33023,
        OLDLACE: 4260751103,
        OLIVE: 2155872511,
        OLIVEDRAB: 1804477439,
        ORANGE: 4289003775,
        ORANGERED: 4282712319,
        ORCHID: 3664828159,
        PALEGOLDENROD: 4008225535,
        PALEGREEN: 2566625535,
        PALETURQUOISE: 2951671551,
        PALEVIOLETRED: 3681588223,
        PAPAYAWHIP: 4293907967,
        PEACHPUFF: 4292524543,
        PERU: 3448061951,
        PINK: 4290825215,
        PLUM: 3718307327,
        POWDERBLUE: 2967529215,
        PURPLE: 2147516671,
        REBECCAPURPLE: 1714657791,
        RED: 4278190335,
        ROSYBROWN: 3163525119,
        ROYALBLUE: 1097458175,
        SADDLEBROWN: 2336560127,
        SALMON: 4202722047,
        SANDYBROWN: 4104413439,
        SEAGREEN: 780883967,
        SEASHELL: 4294307583,
        SIENNA: 2689740287,
        SILVER: 3233857791,
        SKYBLUE: 2278484991,
        SLATEBLUE: 1784335871,
        SLATEGRAY: 1887473919,
        SLATEGREY: 1887473919,
        SNOW: 4294638335,
        SPRINGGREEN: 16744447,
        STEELBLUE: 1182971135,
        TAN: 3535047935,
        TEAL: 8421631,
        THISTLE: 3636451583,
        TOMATO: 4284696575,
        TRANSPARENT: 0,
        TURQUOISE: 1088475391,
        VIOLET: 4001558271,
        WHEAT: 4125012991,
        WHITE: 4294967295,
        WHITESMOKE: 4126537215,
        YELLOW: 4294902015,
        YELLOWGREEN: 2597139199,
    },
    Ni = {
        name: "background-clip",
        initialValue: "border-box",
        prefix: !1,
        type: 1,
        parse: function (t, A) {
            return A.map(function (e) {
                if (x(e))
                    switch (e.value) {
                        case "padding-box":
                            return 1;
                        case "content-box":
                            return 2;
                    }
                return 0;
            });
        },
    },
    Gi = { name: "background-color", initialValue: "transparent", prefix: !1, type: 3, format: "color" },
    Qt = function (t, A) {
        var e = IA.parse(t, A[0]),
            r = A[1];
        return r && R(r) ? { color: e, stop: r } : { color: e, stop: null };
    },
    Jr = function (t, A) {
        var e = t[0],
            r = t[t.length - 1];
        e.stop === null && (e.stop = P), r.stop === null && (r.stop = HA);
        for (var n = [], s = 0, B = 0; B < t.length; B++) {
            var i = t[B].stop;
            if (i !== null) {
                var a = D(i, A);
                a > s ? n.push(a) : n.push(s), (s = a);
            } else n.push(null);
        }
        for (var o = null, B = 0; B < n.length; B++) {
            var c = n[B];
            if (c === null) o === null && (o = B);
            else if (o !== null) {
                for (var l = B - o, g = n[o - 1], w = (c - g) / (l + 1), Q = 1; Q <= l; Q++) n[o + Q - 1] = w * Q;
                o = null;
            }
        }
        return t.map(function (f, H) {
            var d = f.color;
            return { color: d, stop: Math.max(Math.min(1, n[H] / A), 0) };
        });
    },
    Vi = function (t, A, e) {
        var r = A / 2,
            n = e / 2,
            s = D(t[0], A) - r,
            B = n - D(t[1], e);
        return (Math.atan2(B, s) + Math.PI * 2) % (Math.PI * 2);
    },
    ki = function (t, A, e) {
        var r = typeof t == "number" ? t : Vi(t, A, e),
            n = Math.abs(A * Math.sin(r)) + Math.abs(e * Math.cos(r)),
            s = A / 2,
            B = e / 2,
            i = n / 2,
            a = Math.sin(r - Math.PI / 2) * i,
            o = Math.cos(r - Math.PI / 2) * i;
        return [n, s - o, s + o, B - a, B + a];
    },
    nA = function (t, A) {
        return Math.sqrt(t * t + A * A);
    },
    Yr = function (t, A, e, r, n) {
        var s = [
            [0, 0],
            [0, A],
            [t, 0],
            [t, A],
        ];
        return s.reduce(
            function (B, i) {
                var a = i[0],
                    o = i[1],
                    c = nA(e - a, r - o);
                return (n ? c < B.optimumDistance : c > B.optimumDistance)
                    ? { optimumCorner: i, optimumDistance: c }
                    : B;
            },
            { optimumDistance: n ? 1 / 0 : -1 / 0, optimumCorner: null }
        ).optimumCorner;
    },
    Pi = function (t, A, e, r, n) {
        var s = 0,
            B = 0;
        switch (t.size) {
            case 0:
                t.shape === 0
                    ? (s = B = Math.min(Math.abs(A), Math.abs(A - r), Math.abs(e), Math.abs(e - n)))
                    : t.shape === 1 &&
                      ((s = Math.min(Math.abs(A), Math.abs(A - r))), (B = Math.min(Math.abs(e), Math.abs(e - n))));
                break;
            case 2:
                if (t.shape === 0) s = B = Math.min(nA(A, e), nA(A, e - n), nA(A - r, e), nA(A - r, e - n));
                else if (t.shape === 1) {
                    var i = Math.min(Math.abs(e), Math.abs(e - n)) / Math.min(Math.abs(A), Math.abs(A - r)),
                        a = Yr(r, n, A, e, !0),
                        o = a[0],
                        c = a[1];
                    (s = nA(o - A, (c - e) / i)), (B = i * s);
                }
                break;
            case 1:
                t.shape === 0
                    ? (s = B = Math.max(Math.abs(A), Math.abs(A - r), Math.abs(e), Math.abs(e - n)))
                    : t.shape === 1 &&
                      ((s = Math.max(Math.abs(A), Math.abs(A - r))), (B = Math.max(Math.abs(e), Math.abs(e - n))));
                break;
            case 3:
                if (t.shape === 0) s = B = Math.max(nA(A, e), nA(A, e - n), nA(A - r, e), nA(A - r, e - n));
                else if (t.shape === 1) {
                    var i = Math.max(Math.abs(e), Math.abs(e - n)) / Math.max(Math.abs(A), Math.abs(A - r)),
                        l = Yr(r, n, A, e, !1),
                        o = l[0],
                        c = l[1];
                    (s = nA(o - A, (c - e) / i)), (B = i * s);
                }
                break;
        }
        return (
            Array.isArray(t.size) && ((s = D(t.size[0], r)), (B = t.size.length === 2 ? D(t.size[1], n) : s)), [s, B]
        );
    },
    _i = function (t, A) {
        var e = tA(180),
            r = [];
        return (
            oA(A).forEach(function (n, s) {
                if (s === 0) {
                    var B = n[0];
                    if (B.type === 20 && B.value === "to") {
                        e = As(n);
                        return;
                    } else if ($n(B)) {
                        e = ut.parse(t, B);
                        return;
                    }
                }
                var i = Qt(t, n);
                r.push(i);
            }),
            { angle: e, stops: r, type: 1 }
        );
    },
    Ge = function (t, A) {
        var e = tA(180),
            r = [];
        return (
            oA(A).forEach(function (n, s) {
                if (s === 0) {
                    var B = n[0];
                    if (B.type === 20 && ["top", "left", "right", "bottom"].indexOf(B.value) !== -1) {
                        e = As(n);
                        return;
                    } else if ($n(B)) {
                        e = (ut.parse(t, B) + tA(270)) % tA(360);
                        return;
                    }
                }
                var i = Qt(t, n);
                r.push(i);
            }),
            { angle: e, stops: r, type: 1 }
        );
    },
    Xi = function (t, A) {
        var e = tA(180),
            r = [],
            n = 1,
            s = 0,
            B = 3,
            i = [];
        return (
            oA(A).forEach(function (a, o) {
                var c = a[0];
                if (o === 0) {
                    if (x(c) && c.value === "linear") {
                        n = 1;
                        return;
                    } else if (x(c) && c.value === "radial") {
                        n = 2;
                        return;
                    }
                }
                if (c.type === 18) {
                    if (c.name === "from") {
                        var l = IA.parse(t, c.values[0]);
                        r.push({ stop: P, color: l });
                    } else if (c.name === "to") {
                        var l = IA.parse(t, c.values[0]);
                        r.push({ stop: HA, color: l });
                    } else if (c.name === "color-stop") {
                        var g = c.values.filter(jA);
                        if (g.length === 2) {
                            var l = IA.parse(t, g[1]),
                                w = g[0];
                            zA(w) && r.push({ stop: { type: 16, number: w.number * 100, flags: w.flags }, color: l });
                        }
                    }
                }
            }),
            n === 1
                ? { angle: (e + tA(180)) % tA(360), stops: r, type: n }
                : { size: B, shape: s, stops: r, position: i, type: n }
        );
    },
    es = "closest-side",
    ts = "farthest-side",
    rs = "closest-corner",
    ns = "farthest-corner",
    ss = "circle",
    Bs = "ellipse",
    is = "cover",
    as = "contain",
    Ji = function (t, A) {
        var e = 0,
            r = 3,
            n = [],
            s = [];
        return (
            oA(A).forEach(function (B, i) {
                var a = !0;
                if (i === 0) {
                    var o = !1;
                    a = B.reduce(function (l, g) {
                        if (o)
                            if (x(g))
                                switch (g.value) {
                                    case "center":
                                        return s.push(wr), l;
                                    case "top":
                                    case "left":
                                        return s.push(P), l;
                                    case "right":
                                    case "bottom":
                                        return s.push(HA), l;
                                }
                            else (R(g) || yA(g)) && s.push(g);
                        else if (x(g))
                            switch (g.value) {
                                case ss:
                                    return (e = 0), !1;
                                case Bs:
                                    return (e = 1), !1;
                                case "at":
                                    return (o = !0), !1;
                                case es:
                                    return (r = 0), !1;
                                case is:
                                case ts:
                                    return (r = 1), !1;
                                case as:
                                case rs:
                                    return (r = 2), !1;
                                case ns:
                                    return (r = 3), !1;
                            }
                        else if (yA(g) || R(g)) return Array.isArray(r) || (r = []), r.push(g), !1;
                        return l;
                    }, a);
                }
                if (a) {
                    var c = Qt(t, B);
                    n.push(c);
                }
            }),
            { size: r, shape: e, stops: n, position: s, type: 2 }
        );
    },
    Ve = function (t, A) {
        var e = 0,
            r = 3,
            n = [],
            s = [];
        return (
            oA(A).forEach(function (B, i) {
                var a = !0;
                if (
                    (i === 0
                        ? (a = B.reduce(function (c, l) {
                              if (x(l))
                                  switch (l.value) {
                                      case "center":
                                          return s.push(wr), !1;
                                      case "top":
                                      case "left":
                                          return s.push(P), !1;
                                      case "right":
                                      case "bottom":
                                          return s.push(HA), !1;
                                  }
                              else if (R(l) || yA(l)) return s.push(l), !1;
                              return c;
                          }, a))
                        : i === 1 &&
                          (a = B.reduce(function (c, l) {
                              if (x(l))
                                  switch (l.value) {
                                      case ss:
                                          return (e = 0), !1;
                                      case Bs:
                                          return (e = 1), !1;
                                      case as:
                                      case es:
                                          return (r = 0), !1;
                                      case ts:
                                          return (r = 1), !1;
                                      case rs:
                                          return (r = 2), !1;
                                      case is:
                                      case ns:
                                          return (r = 3), !1;
                                  }
                              else if (yA(l) || R(l)) return Array.isArray(r) || (r = []), r.push(l), !1;
                              return c;
                          }, a)),
                    a)
                ) {
                    var o = Qt(t, B);
                    n.push(o);
                }
            }),
            { size: r, shape: e, stops: n, position: s, type: 2 }
        );
    },
    Yi = function (t) {
        return t.type === 1;
    },
    Wi = function (t) {
        return t.type === 2;
    },
    fr = {
        name: "image",
        parse: function (t, A) {
            if (A.type === 22) {
                var e = { url: A.value, type: 0 };
                return t.cache.addImage(A.value), e;
            }
            if (A.type === 18) {
                var r = os[A.name];
                if (typeof r == "undefined")
                    throw new Error('Attempting to parse an unsupported image function "' + A.name + '"');
                return r(t, A.values);
            }
            throw new Error("Unsupported image type " + A.type);
        },
    };
function Zi(t) {
    return !(t.type === 20 && t.value === "none") && (t.type !== 18 || !!os[t.name]);
}
var os = {
        "linear-gradient": _i,
        "-moz-linear-gradient": Ge,
        "-ms-linear-gradient": Ge,
        "-o-linear-gradient": Ge,
        "-webkit-linear-gradient": Ge,
        "radial-gradient": Ji,
        "-moz-radial-gradient": Ve,
        "-ms-radial-gradient": Ve,
        "-o-radial-gradient": Ve,
        "-webkit-radial-gradient": Ve,
        "-webkit-gradient": Xi,
    },
    qi = {
        name: "background-image",
        initialValue: "none",
        type: 1,
        prefix: !1,
        parse: function (t, A) {
            if (A.length === 0) return [];
            var e = A[0];
            return e.type === 20 && e.value === "none"
                ? []
                : A.filter(function (r) {
                      return jA(r) && Zi(r);
                  }).map(function (r) {
                      return fr.parse(t, r);
                  });
        },
    },
    ji = {
        name: "background-origin",
        initialValue: "border-box",
        prefix: !1,
        type: 1,
        parse: function (t, A) {
            return A.map(function (e) {
                if (x(e))
                    switch (e.value) {
                        case "padding-box":
                            return 1;
                        case "content-box":
                            return 2;
                    }
                return 0;
            });
        },
    },
    zi = {
        name: "background-position",
        initialValue: "0% 0%",
        type: 1,
        prefix: !1,
        parse: function (t, A) {
            return oA(A)
                .map(function (e) {
                    return e.filter(R);
                })
                .map(Wn);
        },
    },
    $i = {
        name: "background-repeat",
        initialValue: "repeat",
        prefix: !1,
        type: 1,
        parse: function (t, A) {
            return oA(A)
                .map(function (e) {
                    return e
                        .filter(x)
                        .map(function (r) {
                            return r.value;
                        })
                        .join(" ");
                })
                .map(Aa);
        },
    },
    Aa = function (t) {
        switch (t) {
            case "no-repeat":
                return 1;
            case "repeat-x":
            case "repeat no-repeat":
                return 2;
            case "repeat-y":
            case "no-repeat repeat":
                return 3;
            case "repeat":
            default:
                return 0;
        }
    },
    qA;
(function (t) {
    (t.AUTO = "auto"), (t.CONTAIN = "contain"), (t.COVER = "cover");
})(qA || (qA = {}));
var ea = {
        name: "background-size",
        initialValue: "0",
        prefix: !1,
        type: 1,
        parse: function (t, A) {
            return oA(A).map(function (e) {
                return e.filter(ta);
            });
        },
    },
    ta = function (t) {
        return x(t) || R(t);
    },
    wt = function (t) {
        return { name: "border-" + t + "-color", initialValue: "transparent", prefix: !1, type: 3, format: "color" };
    },
    ra = wt("top"),
    na = wt("right"),
    sa = wt("bottom"),
    Ba = wt("left"),
    ft = function (t) {
        return {
            name: "border-radius-" + t,
            initialValue: "0 0",
            prefix: !1,
            type: 1,
            parse: function (A, e) {
                return Wn(e.filter(R));
            },
        };
    },
    ia = ft("top-left"),
    aa = ft("top-right"),
    oa = ft("bottom-right"),
    ca = ft("bottom-left"),
    Ct = function (t) {
        return {
            name: "border-" + t + "-style",
            initialValue: "solid",
            prefix: !1,
            type: 2,
            parse: function (A, e) {
                switch (e) {
                    case "none":
                        return 0;
                    case "dashed":
                        return 2;
                    case "dotted":
                        return 3;
                    case "double":
                        return 4;
                }
                return 1;
            },
        };
    },
    la = Ct("top"),
    ga = Ct("right"),
    ua = Ct("bottom"),
    Qa = Ct("left"),
    ht = function (t) {
        return {
            name: "border-" + t + "-width",
            initialValue: "0",
            type: 0,
            prefix: !1,
            parse: function (A, e) {
                return de(e) ? e.number : 0;
            },
        };
    },
    wa = ht("top"),
    fa = ht("right"),
    Ca = ht("bottom"),
    ha = ht("left"),
    Ua = { name: "color", initialValue: "transparent", prefix: !1, type: 3, format: "color" },
    Fa = {
        name: "direction",
        initialValue: "ltr",
        prefix: !1,
        type: 2,
        parse: function (t, A) {
            switch (A) {
                case "rtl":
                    return 1;
                case "ltr":
                default:
                    return 0;
            }
        },
    },
    da = {
        name: "display",
        initialValue: "inline-block",
        prefix: !1,
        type: 1,
        parse: function (t, A) {
            return A.filter(x).reduce(function (e, r) {
                return e | pa(r.value);
            }, 0);
        },
    },
    pa = function (t) {
        switch (t) {
            case "block":
            case "-webkit-box":
                return 2;
            case "inline":
                return 4;
            case "run-in":
                return 8;
            case "flow":
                return 16;
            case "flow-root":
                return 32;
            case "table":
                return 64;
            case "flex":
            case "-webkit-flex":
                return 128;
            case "grid":
            case "-ms-grid":
                return 256;
            case "ruby":
                return 512;
            case "subgrid":
                return 1024;
            case "list-item":
                return 2048;
            case "table-row-group":
                return 4096;
            case "table-header-group":
                return 8192;
            case "table-footer-group":
                return 16384;
            case "table-row":
                return 32768;
            case "table-cell":
                return 65536;
            case "table-column-group":
                return 131072;
            case "table-column":
                return 262144;
            case "table-caption":
                return 524288;
            case "ruby-base":
                return 1048576;
            case "ruby-text":
                return 2097152;
            case "ruby-base-container":
                return 4194304;
            case "ruby-text-container":
                return 8388608;
            case "contents":
                return 16777216;
            case "inline-block":
                return 33554432;
            case "inline-list-item":
                return 67108864;
            case "inline-table":
                return 134217728;
            case "inline-flex":
                return 268435456;
            case "inline-grid":
                return 536870912;
        }
        return 0;
    },
    Ea = {
        name: "float",
        initialValue: "none",
        prefix: !1,
        type: 2,
        parse: function (t, A) {
            switch (A) {
                case "left":
                    return 1;
                case "right":
                    return 2;
                case "inline-start":
                    return 3;
                case "inline-end":
                    return 4;
            }
            return 0;
        },
    },
    Ha = {
        name: "letter-spacing",
        initialValue: "0",
        prefix: !1,
        type: 0,
        parse: function (t, A) {
            return A.type === 20 && A.value === "normal" ? 0 : A.type === 17 || A.type === 15 ? A.number : 0;
        },
    },
    tt;
(function (t) {
    (t.NORMAL = "normal"), (t.STRICT = "strict");
})(tt || (tt = {}));
var va = {
        name: "line-break",
        initialValue: "normal",
        prefix: !1,
        type: 2,
        parse: function (t, A) {
            switch (A) {
                case "strict":
                    return tt.STRICT;
                case "normal":
                default:
                    return tt.NORMAL;
            }
        },
    },
    Ia = { name: "line-height", initialValue: "normal", prefix: !1, type: 4 },
    Wr = function (t, A) {
        return x(t) && t.value === "normal" ? 1.2 * A : t.type === 17 ? A * t.number : R(t) ? D(t, A) : A;
    },
    ma = {
        name: "list-style-image",
        initialValue: "none",
        type: 0,
        prefix: !1,
        parse: function (t, A) {
            return A.type === 20 && A.value === "none" ? null : fr.parse(t, A);
        },
    },
    ya = {
        name: "list-style-position",
        initialValue: "outside",
        prefix: !1,
        type: 2,
        parse: function (t, A) {
            switch (A) {
                case "inside":
                    return 0;
                case "outside":
                default:
                    return 1;
            }
        },
    },
    rr = {
        name: "list-style-type",
        initialValue: "none",
        prefix: !1,
        type: 2,
        parse: function (t, A) {
            switch (A) {
                case "disc":
                    return 0;
                case "circle":
                    return 1;
                case "square":
                    return 2;
                case "decimal":
                    return 3;
                case "cjk-decimal":
                    return 4;
                case "decimal-leading-zero":
                    return 5;
                case "lower-roman":
                    return 6;
                case "upper-roman":
                    return 7;
                case "lower-greek":
                    return 8;
                case "lower-alpha":
                    return 9;
                case "upper-alpha":
                    return 10;
                case "arabic-indic":
                    return 11;
                case "armenian":
                    return 12;
                case "bengali":
                    return 13;
                case "cambodian":
                    return 14;
                case "cjk-earthly-branch":
                    return 15;
                case "cjk-heavenly-stem":
                    return 16;
                case "cjk-ideographic":
                    return 17;
                case "devanagari":
                    return 18;
                case "ethiopic-numeric":
                    return 19;
                case "georgian":
                    return 20;
                case "gujarati":
                    return 21;
                case "gurmukhi":
                    return 22;
                case "hebrew":
                    return 22;
                case "hiragana":
                    return 23;
                case "hiragana-iroha":
                    return 24;
                case "japanese-formal":
                    return 25;
                case "japanese-informal":
                    return 26;
                case "kannada":
                    return 27;
                case "katakana":
                    return 28;
                case "katakana-iroha":
                    return 29;
                case "khmer":
                    return 30;
                case "korean-hangul-formal":
                    return 31;
                case "korean-hanja-formal":
                    return 32;
                case "korean-hanja-informal":
                    return 33;
                case "lao":
                    return 34;
                case "lower-armenian":
                    return 35;
                case "malayalam":
                    return 36;
                case "mongolian":
                    return 37;
                case "myanmar":
                    return 38;
                case "oriya":
                    return 39;
                case "persian":
                    return 40;
                case "simp-chinese-formal":
                    return 41;
                case "simp-chinese-informal":
                    return 42;
                case "tamil":
                    return 43;
                case "telugu":
                    return 44;
                case "thai":
                    return 45;
                case "tibetan":
                    return 46;
                case "trad-chinese-formal":
                    return 47;
                case "trad-chinese-informal":
                    return 48;
                case "upper-armenian":
                    return 49;
                case "disclosure-open":
                    return 50;
                case "disclosure-closed":
                    return 51;
                case "none":
                default:
                    return -1;
            }
        },
    },
    Ut = function (t) {
        return { name: "margin-" + t, initialValue: "0", prefix: !1, type: 4 };
    },
    La = Ut("top"),
    Ka = Ut("right"),
    ba = Ut("bottom"),
    xa = Ut("left"),
    Da = {
        name: "overflow",
        initialValue: "visible",
        prefix: !1,
        type: 1,
        parse: function (t, A) {
            return A.filter(x).map(function (e) {
                switch (e.value) {
                    case "hidden":
                        return 1;
                    case "scroll":
                        return 2;
                    case "clip":
                        return 3;
                    case "auto":
                        return 4;
                    case "visible":
                    default:
                        return 0;
                }
            });
        },
    },
    Sa = {
        name: "overflow-wrap",
        initialValue: "normal",
        prefix: !1,
        type: 2,
        parse: function (t, A) {
            switch (A) {
                case "break-word":
                    return "break-word";
                case "normal":
                default:
                    return "normal";
            }
        },
    },
    Ft = function (t) {
        return { name: "padding-" + t, initialValue: "0", prefix: !1, type: 3, format: "length-percentage" };
    },
    Ta = Ft("top"),
    Oa = Ft("right"),
    Ma = Ft("bottom"),
    Ra = Ft("left"),
    Na = {
        name: "text-align",
        initialValue: "left",
        prefix: !1,
        type: 2,
        parse: function (t, A) {
            switch (A) {
                case "right":
                    return 2;
                case "center":
                case "justify":
                    return 1;
                case "left":
                default:
                    return 0;
            }
        },
    },
    Ga = {
        name: "position",
        initialValue: "static",
        prefix: !1,
        type: 2,
        parse: function (t, A) {
            switch (A) {
                case "relative":
                    return 1;
                case "absolute":
                    return 2;
                case "fixed":
                    return 3;
                case "sticky":
                    return 4;
            }
            return 0;
        },
    },
    Va = {
        name: "text-shadow",
        initialValue: "none",
        type: 1,
        prefix: !1,
        parse: function (t, A) {
            return A.length === 1 && tr(A[0], "none")
                ? []
                : oA(A).map(function (e) {
                      for (
                          var r = { color: wA.TRANSPARENT, offsetX: P, offsetY: P, blur: P }, n = 0, s = 0;
                          s < e.length;
                          s++
                      ) {
                          var B = e[s];
                          yA(B)
                              ? (n === 0 ? (r.offsetX = B) : n === 1 ? (r.offsetY = B) : (r.blur = B), n++)
                              : (r.color = IA.parse(t, B));
                      }
                      return r;
                  });
        },
    },
    ka = {
        name: "text-transform",
        initialValue: "none",
        prefix: !1,
        type: 2,
        parse: function (t, A) {
            switch (A) {
                case "uppercase":
                    return 2;
                case "lowercase":
                    return 1;
                case "capitalize":
                    return 3;
            }
            return 0;
        },
    },
    Pa = {
        name: "transform",
        initialValue: "none",
        prefix: !0,
        type: 0,
        parse: function (t, A) {
            if (A.type === 20 && A.value === "none") return null;
            if (A.type === 18) {
                var e = Ja[A.name];
                if (typeof e == "undefined")
                    throw new Error('Attempting to parse an unsupported transform function "' + A.name + '"');
                return e(A.values);
            }
            return null;
        },
    },
    _a = function (t) {
        var A = t
            .filter(function (e) {
                return e.type === 17;
            })
            .map(function (e) {
                return e.number;
            });
        return A.length === 6 ? A : null;
    },
    Xa = function (t) {
        var A = t
                .filter(function (a) {
                    return a.type === 17;
                })
                .map(function (a) {
                    return a.number;
                }),
            e = A[0],
            r = A[1];
        A[2], A[3];
        var n = A[4],
            s = A[5];
        A[6], A[7], A[8], A[9], A[10], A[11];
        var B = A[12],
            i = A[13];
        return A[14], A[15], A.length === 16 ? [e, r, n, s, B, i] : null;
    },
    Ja = { matrix: _a, matrix3d: Xa },
    Zr = { type: 16, number: 50, flags: Fe },
    Ya = [Zr, Zr],
    Wa = {
        name: "transform-origin",
        initialValue: "50% 50%",
        prefix: !0,
        type: 1,
        parse: function (t, A) {
            var e = A.filter(R);
            return e.length !== 2 ? Ya : [e[0], e[1]];
        },
    },
    Za = {
        name: "visible",
        initialValue: "none",
        prefix: !1,
        type: 2,
        parse: function (t, A) {
            switch (A) {
                case "hidden":
                    return 1;
                case "collapse":
                    return 2;
                case "visible":
                default:
                    return 0;
            }
        },
    },
    Qe;
(function (t) {
    (t.NORMAL = "normal"), (t.BREAK_ALL = "break-all"), (t.KEEP_ALL = "keep-all");
})(Qe || (Qe = {}));
var qa = {
        name: "word-break",
        initialValue: "normal",
        prefix: !1,
        type: 2,
        parse: function (t, A) {
            switch (A) {
                case "break-all":
                    return Qe.BREAK_ALL;
                case "keep-all":
                    return Qe.KEEP_ALL;
                case "normal":
                default:
                    return Qe.NORMAL;
            }
        },
    },
    ja = {
        name: "z-index",
        initialValue: "auto",
        prefix: !1,
        type: 0,
        parse: function (t, A) {
            if (A.type === 20) return { auto: !0, order: 0 };
            if (zA(A)) return { auto: !1, order: A.number };
            throw new Error("Invalid z-index number parsed");
        },
    },
    cs = {
        name: "time",
        parse: function (t, A) {
            if (A.type === 15)
                switch (A.unit.toLowerCase()) {
                    case "s":
                        return 1e3 * A.number;
                    case "ms":
                        return A.number;
                }
            throw new Error("Unsupported time type");
        },
    },
    za = {
        name: "opacity",
        initialValue: "1",
        type: 0,
        prefix: !1,
        parse: function (t, A) {
            return zA(A) ? A.number : 1;
        },
    },
    $a = { name: "text-decoration-color", initialValue: "transparent", prefix: !1, type: 3, format: "color" },
    Ao = {
        name: "text-decoration-line",
        initialValue: "none",
        prefix: !1,
        type: 1,
        parse: function (t, A) {
            return A.filter(x)
                .map(function (e) {
                    switch (e.value) {
                        case "underline":
                            return 1;
                        case "overline":
                            return 2;
                        case "line-through":
                            return 3;
                        case "none":
                            return 4;
                    }
                    return 0;
                })
                .filter(function (e) {
                    return e !== 0;
                });
        },
    },
    eo = {
        name: "font-family",
        initialValue: "",
        prefix: !1,
        type: 1,
        parse: function (t, A) {
            var e = [],
                r = [];
            return (
                A.forEach(function (n) {
                    switch (n.type) {
                        case 20:
                        case 0:
                            e.push(n.value);
                            break;
                        case 17:
                            e.push(n.number.toString());
                            break;
                        case 4:
                            r.push(e.join(" ")), (e.length = 0);
                            break;
                    }
                }),
                e.length && r.push(e.join(" ")),
                r.map(function (n) {
                    return n.indexOf(" ") === -1 ? n : "'" + n + "'";
                })
            );
        },
    },
    to = { name: "font-size", initialValue: "0", prefix: !1, type: 3, format: "length" },
    ro = {
        name: "font-weight",
        initialValue: "normal",
        type: 0,
        prefix: !1,
        parse: function (t, A) {
            if (zA(A)) return A.number;
            if (x(A))
                switch (A.value) {
                    case "bold":
                        return 700;
                    case "normal":
                    default:
                        return 400;
                }
            return 400;
        },
    },
    no = {
        name: "font-variant",
        initialValue: "none",
        type: 1,
        prefix: !1,
        parse: function (t, A) {
            return A.filter(x).map(function (e) {
                return e.value;
            });
        },
    },
    so = {
        name: "font-style",
        initialValue: "normal",
        prefix: !1,
        type: 2,
        parse: function (t, A) {
            switch (A) {
                case "oblique":
                    return "oblique";
                case "italic":
                    return "italic";
                case "normal":
                default:
                    return "normal";
            }
        },
    },
    N = function (t, A) {
        return (t & A) !== 0;
    },
    Bo = {
        name: "content",
        initialValue: "none",
        type: 1,
        prefix: !1,
        parse: function (t, A) {
            if (A.length === 0) return [];
            var e = A[0];
            return e.type === 20 && e.value === "none" ? [] : A;
        },
    },
    io = {
        name: "counter-increment",
        initialValue: "none",
        prefix: !0,
        type: 1,
        parse: function (t, A) {
            if (A.length === 0) return null;
            var e = A[0];
            if (e.type === 20 && e.value === "none") return null;
            for (var r = [], n = A.filter(Yn), s = 0; s < n.length; s++) {
                var B = n[s],
                    i = n[s + 1];
                if (B.type === 20) {
                    var a = i && zA(i) ? i.number : 1;
                    r.push({ counter: B.value, increment: a });
                }
            }
            return r;
        },
    },
    ao = {
        name: "counter-reset",
        initialValue: "none",
        prefix: !0,
        type: 1,
        parse: function (t, A) {
            if (A.length === 0) return [];
            for (var e = [], r = A.filter(Yn), n = 0; n < r.length; n++) {
                var s = r[n],
                    B = r[n + 1];
                if (x(s) && s.value !== "none") {
                    var i = B && zA(B) ? B.number : 0;
                    e.push({ counter: s.value, reset: i });
                }
            }
            return e;
        },
    },
    oo = {
        name: "duration",
        initialValue: "0s",
        prefix: !1,
        type: 1,
        parse: function (t, A) {
            return A.filter(de).map(function (e) {
                return cs.parse(t, e);
            });
        },
    },
    co = {
        name: "quotes",
        initialValue: "none",
        prefix: !0,
        type: 1,
        parse: function (t, A) {
            if (A.length === 0) return null;
            var e = A[0];
            if (e.type === 20 && e.value === "none") return null;
            var r = [],
                n = A.filter(Oi);
            if (n.length % 2 !== 0) return null;
            for (var s = 0; s < n.length; s += 2) {
                var B = n[s].value,
                    i = n[s + 1].value;
                r.push({ open: B, close: i });
            }
            return r;
        },
    },
    qr = function (t, A, e) {
        if (!t) return "";
        var r = t[Math.min(A, t.length - 1)];
        return r ? (e ? r.open : r.close) : "";
    },
    lo = {
        name: "box-shadow",
        initialValue: "none",
        type: 1,
        prefix: !1,
        parse: function (t, A) {
            return A.length === 1 && tr(A[0], "none")
                ? []
                : oA(A).map(function (e) {
                      for (
                          var r = { color: 255, offsetX: P, offsetY: P, blur: P, spread: P, inset: !1 }, n = 0, s = 0;
                          s < e.length;
                          s++
                      ) {
                          var B = e[s];
                          tr(B, "inset")
                              ? (r.inset = !0)
                              : yA(B)
                              ? (n === 0
                                    ? (r.offsetX = B)
                                    : n === 1
                                    ? (r.offsetY = B)
                                    : n === 2
                                    ? (r.blur = B)
                                    : (r.spread = B),
                                n++)
                              : (r.color = IA.parse(t, B));
                      }
                      return r;
                  });
        },
    },
    go = {
        name: "paint-order",
        initialValue: "normal",
        prefix: !1,
        type: 1,
        parse: function (t, A) {
            var e = [0, 1, 2],
                r = [];
            return (
                A.filter(x).forEach(function (n) {
                    switch (n.value) {
                        case "stroke":
                            r.push(1);
                            break;
                        case "fill":
                            r.push(0);
                            break;
                        case "markers":
                            r.push(2);
                            break;
                    }
                }),
                e.forEach(function (n) {
                    r.indexOf(n) === -1 && r.push(n);
                }),
                r
            );
        },
    },
    uo = { name: "-webkit-text-stroke-color", initialValue: "currentcolor", prefix: !1, type: 3, format: "color" },
    Qo = {
        name: "-webkit-text-stroke-width",
        initialValue: "0",
        type: 0,
        prefix: !1,
        parse: function (t, A) {
            return de(A) ? A.number : 0;
        },
    },
    wo = (function () {
        function t(A, e) {
            var r, n;
            (this.animationDuration = U(A, oo, e.animationDuration)),
                (this.backgroundClip = U(A, Ni, e.backgroundClip)),
                (this.backgroundColor = U(A, Gi, e.backgroundColor)),
                (this.backgroundImage = U(A, qi, e.backgroundImage)),
                (this.backgroundOrigin = U(A, ji, e.backgroundOrigin)),
                (this.backgroundPosition = U(A, zi, e.backgroundPosition)),
                (this.backgroundRepeat = U(A, $i, e.backgroundRepeat)),
                (this.backgroundSize = U(A, ea, e.backgroundSize)),
                (this.borderTopColor = U(A, ra, e.borderTopColor)),
                (this.borderRightColor = U(A, na, e.borderRightColor)),
                (this.borderBottomColor = U(A, sa, e.borderBottomColor)),
                (this.borderLeftColor = U(A, Ba, e.borderLeftColor)),
                (this.borderTopLeftRadius = U(A, ia, e.borderTopLeftRadius)),
                (this.borderTopRightRadius = U(A, aa, e.borderTopRightRadius)),
                (this.borderBottomRightRadius = U(A, oa, e.borderBottomRightRadius)),
                (this.borderBottomLeftRadius = U(A, ca, e.borderBottomLeftRadius)),
                (this.borderTopStyle = U(A, la, e.borderTopStyle)),
                (this.borderRightStyle = U(A, ga, e.borderRightStyle)),
                (this.borderBottomStyle = U(A, ua, e.borderBottomStyle)),
                (this.borderLeftStyle = U(A, Qa, e.borderLeftStyle)),
                (this.borderTopWidth = U(A, wa, e.borderTopWidth)),
                (this.borderRightWidth = U(A, fa, e.borderRightWidth)),
                (this.borderBottomWidth = U(A, Ca, e.borderBottomWidth)),
                (this.borderLeftWidth = U(A, ha, e.borderLeftWidth)),
                (this.boxShadow = U(A, lo, e.boxShadow)),
                (this.color = U(A, Ua, e.color)),
                (this.direction = U(A, Fa, e.direction)),
                (this.display = U(A, da, e.display)),
                (this.float = U(A, Ea, e.cssFloat)),
                (this.fontFamily = U(A, eo, e.fontFamily)),
                (this.fontSize = U(A, to, e.fontSize)),
                (this.fontStyle = U(A, so, e.fontStyle)),
                (this.fontVariant = U(A, no, e.fontVariant)),
                (this.fontWeight = U(A, ro, e.fontWeight)),
                (this.letterSpacing = U(A, Ha, e.letterSpacing)),
                (this.lineBreak = U(A, va, e.lineBreak)),
                (this.lineHeight = U(A, Ia, e.lineHeight)),
                (this.listStyleImage = U(A, ma, e.listStyleImage)),
                (this.listStylePosition = U(A, ya, e.listStylePosition)),
                (this.listStyleType = U(A, rr, e.listStyleType)),
                (this.marginTop = U(A, La, e.marginTop)),
                (this.marginRight = U(A, Ka, e.marginRight)),
                (this.marginBottom = U(A, ba, e.marginBottom)),
                (this.marginLeft = U(A, xa, e.marginLeft)),
                (this.opacity = U(A, za, e.opacity));
            var s = U(A, Da, e.overflow);
            (this.overflowX = s[0]),
                (this.overflowY = s[s.length > 1 ? 1 : 0]),
                (this.overflowWrap = U(A, Sa, e.overflowWrap)),
                (this.paddingTop = U(A, Ta, e.paddingTop)),
                (this.paddingRight = U(A, Oa, e.paddingRight)),
                (this.paddingBottom = U(A, Ma, e.paddingBottom)),
                (this.paddingLeft = U(A, Ra, e.paddingLeft)),
                (this.paintOrder = U(A, go, e.paintOrder)),
                (this.position = U(A, Ga, e.position)),
                (this.textAlign = U(A, Na, e.textAlign)),
                (this.textDecorationColor = U(
                    A,
                    $a,
                    (r = e.textDecorationColor) !== null && r !== void 0 ? r : e.color
                )),
                (this.textDecorationLine = U(
                    A,
                    Ao,
                    (n = e.textDecorationLine) !== null && n !== void 0 ? n : e.textDecoration
                )),
                (this.textShadow = U(A, Va, e.textShadow)),
                (this.textTransform = U(A, ka, e.textTransform)),
                (this.transform = U(A, Pa, e.transform)),
                (this.transformOrigin = U(A, Wa, e.transformOrigin)),
                (this.visibility = U(A, Za, e.visibility)),
                (this.webkitTextStrokeColor = U(A, uo, e.webkitTextStrokeColor)),
                (this.webkitTextStrokeWidth = U(A, Qo, e.webkitTextStrokeWidth)),
                (this.wordBreak = U(A, qa, e.wordBreak)),
                (this.zIndex = U(A, ja, e.zIndex));
        }
        return (
            (t.prototype.isVisible = function () {
                return this.display > 0 && this.opacity > 0 && this.visibility === 0;
            }),
            (t.prototype.isTransparent = function () {
                return mA(this.backgroundColor);
            }),
            (t.prototype.isTransformed = function () {
                return this.transform !== null;
            }),
            (t.prototype.isPositioned = function () {
                return this.position !== 0;
            }),
            (t.prototype.isPositionedWithZIndex = function () {
                return this.isPositioned() && !this.zIndex.auto;
            }),
            (t.prototype.isFloating = function () {
                return this.float !== 0;
            }),
            (t.prototype.isInlineLevel = function () {
                return (
                    N(this.display, 4) ||
                    N(this.display, 33554432) ||
                    N(this.display, 268435456) ||
                    N(this.display, 536870912) ||
                    N(this.display, 67108864) ||
                    N(this.display, 134217728)
                );
            }),
            t
        );
    })(),
    fo = (function () {
        function t(A, e) {
            (this.content = U(A, Bo, e.content)), (this.quotes = U(A, co, e.quotes));
        }
        return t;
    })(),
    jr = (function () {
        function t(A, e) {
            (this.counterIncrement = U(A, io, e.counterIncrement)), (this.counterReset = U(A, ao, e.counterReset));
        }
        return t;
    })(),
    U = function (t, A, e) {
        var r = new Xn(),
            n = e !== null && typeof e != "undefined" ? e.toString() : A.initialValue;
        r.write(n);
        var s = new Jn(r.read());
        switch (A.type) {
            case 2:
                var B = s.parseComponentValue();
                return A.parse(t, x(B) ? B.value : A.initialValue);
            case 0:
                return A.parse(t, s.parseComponentValue());
            case 1:
                return A.parse(t, s.parseComponentValues());
            case 4:
                return s.parseComponentValue();
            case 3:
                switch (A.format) {
                    case "angle":
                        return ut.parse(t, s.parseComponentValue());
                    case "color":
                        return IA.parse(t, s.parseComponentValue());
                    case "image":
                        return fr.parse(t, s.parseComponentValue());
                    case "length":
                        var i = s.parseComponentValue();
                        return yA(i) ? i : P;
                    case "length-percentage":
                        var a = s.parseComponentValue();
                        return R(a) ? a : P;
                    case "time":
                        return cs.parse(t, s.parseComponentValue());
                }
                break;
        }
    },
    Co = "data-html2canvas-debug",
    ho = function (t) {
        var A = t.getAttribute(Co);
        switch (A) {
            case "all":
                return 1;
            case "clone":
                return 2;
            case "parse":
                return 3;
            case "render":
                return 4;
            default:
                return 0;
        }
    },
    nr = function (t, A) {
        var e = ho(t);
        return e === 1 || A === e;
    },
    cA = (function () {
        function t(A, e) {
            if (((this.context = A), (this.textNodes = []), (this.elements = []), (this.flags = 0), nr(e, 3))) debugger;
            (this.styles = new wo(A, window.getComputedStyle(e, null))),
                ir(e) &&
                    (this.styles.animationDuration.some(function (r) {
                        return r > 0;
                    }) && (e.style.animationDuration = "0s"),
                    this.styles.transform !== null && (e.style.transform = "none")),
                (this.bounds = lt(this.context, e)),
                nr(e, 4) && (this.flags |= 16);
        }
        return t;
    })(),
    Uo =
        "AAAAAAAAAAAAEA4AGBkAAFAaAAACAAAAAAAIABAAGAAwADgACAAQAAgAEAAIABAACAAQAAgAEAAIABAACAAQAAgAEAAIABAAQABIAEQATAAIABAACAAQAAgAEAAIABAAVABcAAgAEAAIABAACAAQAGAAaABwAHgAgACIAI4AlgAIABAAmwCjAKgAsAC2AL4AvQDFAMoA0gBPAVYBWgEIAAgACACMANoAYgFkAWwBdAF8AX0BhQGNAZUBlgGeAaMBlQGWAasBswF8AbsBwwF0AcsBYwHTAQgA2wG/AOMBdAF8AekB8QF0AfkB+wHiAHQBfAEIAAMC5gQIAAsCEgIIAAgAFgIeAggAIgIpAggAMQI5AkACygEIAAgASAJQAlgCYAIIAAgACAAKBQoFCgUTBRMFGQUrBSsFCAAIAAgACAAIAAgACAAIAAgACABdAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACABoAmgCrwGvAQgAbgJ2AggAHgEIAAgACADnAXsCCAAIAAgAgwIIAAgACAAIAAgACACKAggAkQKZAggAPADJAAgAoQKkAqwCsgK6AsICCADJAggA0AIIAAgACAAIANYC3gIIAAgACAAIAAgACABAAOYCCAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAkASoB+QIEAAgACAA8AEMCCABCBQgACABJBVAFCAAIAAgACAAIAAgACAAIAAgACABTBVoFCAAIAFoFCABfBWUFCAAIAAgACAAIAAgAbQUIAAgACAAIAAgACABzBXsFfQWFBYoFigWKBZEFigWKBYoFmAWfBaYFrgWxBbkFCAAIAAgACAAIAAgACAAIAAgACAAIAMEFCAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAMgFCADQBQgACAAIAAgACAAIAAgACAAIAAgACAAIAO4CCAAIAAgAiQAIAAgACABAAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAD0AggACAD8AggACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIANYFCAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAMDvwAIAAgAJAIIAAgACAAIAAgACAAIAAgACwMTAwgACAB9BOsEGwMjAwgAKwMyAwsFYgE3A/MEPwMIAEUDTQNRAwgAWQOsAGEDCAAIAAgACAAIAAgACABpAzQFNQU2BTcFOAU5BToFNAU1BTYFNwU4BTkFOgU0BTUFNgU3BTgFOQU6BTQFNQU2BTcFOAU5BToFNAU1BTYFNwU4BTkFOgU0BTUFNgU3BTgFOQU6BTQFNQU2BTcFOAU5BToFNAU1BTYFNwU4BTkFOgU0BTUFNgU3BTgFOQU6BTQFNQU2BTcFOAU5BToFNAU1BTYFNwU4BTkFOgU0BTUFNgU3BTgFOQU6BTQFNQU2BTcFOAU5BToFNAU1BTYFNwU4BTkFOgU0BTUFNgU3BTgFOQU6BTQFNQU2BTcFOAU5BToFNAU1BTYFNwU4BTkFOgU0BTUFNgU3BTgFOQU6BTQFNQU2BTcFOAU5BToFNAU1BTYFNwU4BTkFOgU0BTUFNgU3BTgFOQU6BTQFNQU2BTcFOAU5BToFNAU1BTYFNwU4BTkFOgU0BTUFNgU3BTgFOQU6BTQFNQU2BTcFOAU5BToFNAU1BTYFNwU4BTkFOgU0BTUFNgU3BTgFOQU6BTQFNQU2BTcFOAU5BToFNAU1BTYFNwU4BTkFOgU0BTUFNgU3BTgFOQU6BTQFNQU2BTcFOAU5BToFNAU1BTYFNwU4BTkFOgU0BTUFNgU3BTgFOQU6BTQFNQU2BTcFOAU5BToFNAU1BTYFNwU4BTkFOgU0BTUFNgU3BTgFOQU6BTQFNQU2BTcFOAU5BToFNAU1BTYFNwU4BTkFOgU0BTUFNgU3BTgFOQU6BTQFNQU2BTcFOAU5BToFNAU1BTYFNwU4BTkFOgU0BTUFNgU3BTgFOQU6BTQFNQU2BTcFOAU5BToFNAU1BTYFNwU4BTkFOgU0BTUFNgU3BTgFOQU6BTQFNQU2BTcFOAU5BToFNAU1BTYFNwU4BTkFOgU0BTUFNgU3BTgFOQU6BTQFNQU2BTcFOAU5BToFNAU1BTYFNwU4BTkFIQUoBSwFCAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACABtAwgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACABMAEwACAAIAAgACAAIABgACAAIAAgACAC/AAgACAAyAQgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACACAAIAAwAAgACAAIAAgACAAIAAgACAAIAAAARABIAAgACAAIABQASAAIAAgAIABwAEAAjgCIABsAqAC2AL0AigDQAtwC+IJIQqVAZUBWQqVAZUBlQGVAZUBlQGrC5UBlQGVAZUBlQGVAZUBlQGVAXsKlQGVAbAK6wsrDGUMpQzlDJUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAZUBlQGVAfAKAAuZA64AtwCJALoC6ADwAAgAuACgA/oEpgO6AqsD+AAIAAgAswMIAAgACAAIAIkAuwP5AfsBwwPLAwgACAAIAAgACADRA9kDCAAIAOED6QMIAAgACAAIAAgACADuA/YDCAAIAP4DyQAIAAgABgQIAAgAXQAOBAgACAAIAAgACAAIABMECAAIAAgACAAIAAgACAD8AAQBCAAIAAgAGgQiBCoECAExBAgAEAEIAAgACAAIAAgACAAIAAgACAAIAAgACAA4BAgACABABEYECAAIAAgATAQYAQgAVAQIAAgACAAIAAgACAAIAAgACAAIAFoECAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAOQEIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAB+BAcACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAEABhgSMBAgACAAIAAgAlAQIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAwAEAAQABAADAAMAAwADAAQABAAEAAQABAAEAAQABHATAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAdQMIAAgACAAIAAgACAAIAMkACAAIAAgAfQMIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACACFA4kDCAAIAAgACAAIAOcBCAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAIcDCAAIAAgACAAIAAgACAAIAAgACAAIAJEDCAAIAAgACADFAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACABgBAgAZgQIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAbAQCBXIECAAIAHkECAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACABAAJwEQACjBKoEsgQIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAC6BMIECAAIAAgACAAIAAgACABmBAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAxwQIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAGYECAAIAAgAzgQIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAigWKBYoFigWKBYoFigWKBd0FXwUIAOIF6gXxBYoF3gT5BQAGCAaKBYoFigWKBYoFigWKBYoFigWKBYoFigXWBIoFigWKBYoFigWKBYoFigWKBYsFEAaKBYoFigWKBYoFigWKBRQGCACKBYoFigWKBQgACAAIANEECAAIABgGigUgBggAJgYIAC4GMwaKBYoF0wQ3Bj4GigWKBYoFigWKBYoFigWKBYoFigWKBYoFigUIAAgACAAIAAgACAAIAAgAigWKBYoFigWKBYoFigWKBYoFigWKBYoFigWKBYoFigWKBYoFigWKBYoFigWKBYoFigWKBYoFigWKBYoFigWLBf///////wQABAAEAAQABAAEAAQABAAEAAQAAwAEAAQAAgAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAAAAAAAAAAAAAAAAAAAAAAAAAOAAAAAAAAAAQADgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUABQAFAAUABQAFAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAAAAUAAAAFAAUAAAAFAAUAAAAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAEAAQABAAEAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAUABQAFAAUABQAFAAUABQAFAAUABQAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUABQAFAAUABQAFAAUAAQAAAAUABQAFAAUABQAFAAAAAAAFAAUAAAAFAAUABQAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEAAAAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAUABQAFAAUABQAFAAUABQAFAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAUABQAFAAUABQAFAAUABQAAAAAAAAAAAAAAAAAAAAAAAAAFAAAAAAAFAAUAAQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABwAFAAUABQAFAAAABwAHAAcAAAAHAAcABwAFAAEAAAAAAAAAAAAAAAAAAAAAAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAAcABwAFAAUABQAFAAcABwAFAAUAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAAAAAQABAAAAAAAAAAAAAAAFAAUABQAFAAAABwAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAHAAcABwAHAAcAAAAHAAcAAAAAAAUABQAHAAUAAQAHAAEABwAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAFAAUABQAFAAUABwABAAUABQAFAAUAAAAAAAAAAAAAAAEAAQABAAEAAQABAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABwAFAAUAAAAAAAAAAAAAAAAABQAFAAUABQAFAAUAAQAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUABQAFAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQABQANAAQABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQABAAEAAQABAAEAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAEAAQABAAEAAQABAAEAAQABAAEAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEAAQABAAEAAQABAAEAAQABAAAAAAAAAAAAAAAAAAAAAAABQAHAAUABQAFAAAAAAAAAAcABQAFAAUABQAFAAQABAAEAAQABAAEAAQABAAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUABQAFAAUAAAAFAAUABQAFAAUAAAAFAAUABQAAAAUABQAFAAUABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAUABQAAAAAAAAAAAAUABQAFAAcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAHAAUAAAAHAAcABwAFAAUABQAFAAUABQAFAAUABwAHAAcABwAFAAcABwAAAAUABQAFAAUABQAFAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUABwAHAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAAAAUABwAHAAUABQAFAAUAAAAAAAcABwAAAAAABwAHAAUAAAAAAAAAAAAAAAAAAAAAAAAABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAUABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAAAAAABQAFAAcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAAABwAHAAcABQAFAAAAAAAAAAAABQAFAAAAAAAFAAUABQAAAAAAAAAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUABQAAAAAAAAAFAAAAAAAAAAAAAAAAAAAAAAAAAAAABwAFAAUABQAFAAUAAAAFAAUABwAAAAcABwAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAUABQAFAAUABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUAAAAFAAUABwAFAAUABQAFAAAAAAAHAAcAAAAAAAcABwAFAAAAAAAAAAAAAAAAAAAABQAFAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAcABwAAAAAAAAAHAAcABwAAAAcABwAHAAUAAAAAAAAAAAAAAAAAAAAAAAAABQAAAAAAAAAAAAAAAAAAAAAABQAHAAcABwAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUABwAHAAcABwAAAAUABQAFAAAABQAFAAUABQAAAAAAAAAAAAAAAAAAAAUABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAAAAcABQAHAAcABQAHAAcAAAAFAAcABwAAAAcABwAFAAUAAAAAAAAAAAAAAAAAAAAFAAUAAAAAAAAAAAAAAAAAAAAAAAAABQAFAAcABwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUABQAAAAUABwAAAAAAAAAAAAAAAAAAAAAAAAAAAAUAAAAAAAAAAAAFAAcABwAFAAUABQAAAAUAAAAHAAcABwAHAAcABwAHAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUAAAAHAAUABQAFAAUABQAFAAUAAAAAAAAAAAAAAAAAAAAAAAUABQAFAAUABQAFAAUABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAAABwAFAAUABQAFAAUABQAFAAUABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAFAAUABQAFAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAAAAUAAAAFAAAAAAAAAAAABwAHAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABwAFAAUABQAFAAUAAAAFAAUAAAAAAAAAAAAAAAUABQAFAAUABQAFAAUABQAFAAUABQAAAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUABQAFAAUABwAFAAUABQAFAAUABQAAAAUABQAHAAcABQAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAAcABQAFAAAAAAAAAAAABQAFAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAUABQAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAAAAcABQAFAAAAAAAAAAAAAAAAAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAFAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUABQAHAAUABQAFAAUABQAFAAUABwAHAAcABwAHAAcABwAHAAUABwAHAAUABQAFAAUABQAFAAUABQAFAAUABQAAAAAAAAAAAAAAAAAAAAAAAAAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAFAAUABwAHAAcABwAFAAUABwAHAAcAAAAAAAAAAAAHAAcABQAHAAcABwAHAAcABwAFAAUABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAFAAcABwAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAcABQAHAAUABQAFAAUABQAFAAUAAAAFAAAABQAAAAAABQAFAAUABQAFAAUABQAFAAcABwAHAAcABwAHAAUABQAFAAUABQAFAAUABQAFAAUAAAAAAAUABQAFAAUABQAHAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUABQAFAAUABQAFAAUABwAFAAcABwAHAAcABwAFAAcABwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAUABQAFAAUABQAFAAUABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAUABwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAAUABQAFAAUABwAHAAUABQAHAAUABQAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAcABQAFAAcABwAHAAUABwAFAAUABQAHAAcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABwAHAAcABwAHAAcABwAHAAUABQAFAAUABQAFAAUABQAHAAcABQAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAFAAUAAAAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAcABQAFAAUABQAFAAUABQAAAAAAAAAAAAUAAAAAAAAAAAAAAAAABQAAAAAABwAFAAUAAAAAAAAAAAAAAAAABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAAABQAFAAUABQAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUABQAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAFAAUABQAFAAUADgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUABQAFAAUAAAAFAAUABQAFAAUABQAFAAUABQAFAAAAAAAAAAAABQAAAAAAAAAFAAAAAAAAAAAABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABwAHAAUABQAHAAAAAAAAAAAABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAcABwAHAAcABQAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUAAAAAAAAAAAAAAAAABQAFAAUABQAFAAUABQAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUABQAFAAUABQAFAAUABQAFAAUABQAHAAcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAcABwAFAAUABQAFAAcABwAFAAUABwAHAAAAAAAAAAAAAAAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUABQAFAAUABQAFAAcABwAFAAUABwAHAAUABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAAAAAAAAAAAAAAAAAAAAAAFAAcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUAAAAFAAUABQAAAAAABQAFAAAAAAAAAAAAAAAFAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAcABQAFAAcABwAAAAAAAAAAAAAABwAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAcABwAFAAcABwAFAAcABwAAAAcABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUABQAFAAUABQAAAAAAAAAAAAAAAAAFAAUABQAAAAUABQAAAAAAAAAAAAAABQAFAAUABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAUABQAAAAAAAAAAAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAcABQAHAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAUABQAFAAUABwAFAAUABQAFAAUABQAFAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABwAHAAcABQAFAAUABQAFAAUABQAFAAUABwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAAcABwAFAAUABQAHAAcABQAHAAUABQAAAAAAAAAAAAAAAAAFAAAABwAHAAcABQAFAAUABQAFAAUABQAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUABwAHAAcABwAAAAAABwAHAAAAAAAHAAcABwAAAAAAAAAAAAAAAAAAAAAAAAAFAAAAAAAAAAAAAAAAAAAAAAAAAAAABwAHAAAAAAAFAAUABQAFAAUABQAFAAAAAAAAAAUABQAFAAUABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAAcABwAFAAUABQAFAAUABQAFAAUABwAHAAUABQAFAAcABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAHAAcABQAFAAUABQAFAAUABwAFAAcABwAFAAcABQAFAAcABQAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAHAAcABQAFAAUABQAAAAAABwAHAAcABwAFAAUABwAFAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAcABwAHAAUABQAFAAUABQAFAAUABQAHAAcABQAHAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUABwAFAAcABwAFAAUABQAFAAUABQAHAAUAAAAAAAAAAAAAAAAAAAAAAAcABwAFAAUABQAFAAcABQAFAAUABQAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAAcABwAFAAUABQAFAAUABQAFAAUABQAHAAUABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAAcABwAFAAUABQAFAAAAAAAFAAUABwAHAAcABwAFAAAAAAAAAAcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAUABQAFAAUABQAFAAUABQAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUAAAAAAAAAAAAAAAAAAAAAAAAABQAFAAUABQAFAAUABwAHAAUABQAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAcABQAFAAUABQAFAAUABQAAAAUABQAFAAUABQAFAAcABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUAAAAHAAUABQAFAAUABQAFAAUABwAFAAUABwAFAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAFAAUABQAFAAUAAAAAAAAABQAAAAUABQAAAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAAcABwAHAAcAAAAFAAUAAAAHAAcABQAHAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAUABwAHAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAUABQAFAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAUABQAFAAUABQAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAAAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAAAAAAAAAAAAAAAAAAABQAFAAUABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAcABwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUABQAAAAUABQAFAAAAAAAFAAUABQAFAAUABQAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAFAAUABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAFAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAAAAAAAAAAABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAAAAAAAAAAAAAAAAAAAAAAFAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUABQAFAAUABQAAAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAFAAUABQAFAAUABQAAAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAFAAUABQAAAAAABQAFAAUABQAFAAUABQAAAAUABQAAAAUABQAFAAUABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAUABQAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAFAAUABQAFAAUABQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAFAAUABQAFAAUADgAOAA4ADgAOAA4ADwAPAA8ADwAPAA8ADwAPAA8ADwAPAA8ADwAPAA8ADwAPAA8ADwAPAA8ADwAPAA8ADwAPAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAcABwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABwAHAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAcABwAHAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAAAAAAAAAkACQAJAAkACQAJAAkACQAJAAkACQAJAAkACQAJAAkACQAJAAkACQAJAAkACQAJAAkACQAJAAkACQAJAAkACQAKAAoACgAKAAoACgAKAAoACgAKAAoACgAKAAoACgAKAAoACgAKAAoACgAKAAoACgAMAAwADAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAkACQAJAAkACQAJAAkACQAJAAkACQAJAAkACQAJAAkACQAJAAkAAAAAAAAAAAAKAAoACgAKAAoACgAKAAoACgAKAAoACgAKAAoACgAKAAoACgAKAAoACgAKAAoACgAKAAoACgAKAAoACgAKAAoACgAAAAAAAAAAAAsADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwACwAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAMAAwADAAAAAAADgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA4AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOAA4ADgAOAA4ADgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADgAOAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA4ADgAAAAAAAAAAAAAAAAAAAAAADgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADgAOAA4ADgAOAA4ADgAOAA4ADgAOAAAAAAAAAAAADgAOAA4AAAAAAAAAAAAAAAAAAAAOAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADgAOAAAAAAAAAAAAAAAAAAAAAAAAAAAADgAAAAAAAAAAAAAAAAAAAAAAAAAOAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADgAOAA4ADgAAAA4ADgAOAA4ADgAOAAAADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4AAAAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAAAAAAAAAAAAAAAAAAAAAAAAAAAADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4AAAAAAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAAAA4AAAAOAAAAAAAAAAAAAAAAAA4AAAAAAAAAAAAAAAAADgAAAAAAAAAAAAAAAAAAAAAAAAAAAA4ADgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADgAAAAAADgAAAAAAAAAAAA4AAAAOAAAAAAAAAAAADgAOAA4AAAAOAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOAA4ADgAOAA4AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOAA4ADgAAAAAAAAAAAAAAAAAAAAAAAAAOAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOAA4AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA4ADgAOAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADgAOAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADgAAAAAAAAAAAA4AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOAAAADgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOAA4ADgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA4ADgAOAA4ADgAOAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA4ADgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADgAAAAAADgAOAA4ADgAOAA4ADgAOAA4ADgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAAAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAAAAAAAAAAAAAAAAAAAAAAAAAAAADgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA4AAAAAAA4ADgAOAA4ADgAOAA4ADgAOAAAADgAOAA4ADgAAAAAAAAAAAAAAAAAAAAAAAAAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4AAAAAAAAAAAAAAAAADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOAA4ADgAOAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADgAOAA4ADgAOAA4ADgAOAAAAAAAAAAAAAAAAAAAAAAAAAAAADgAOAA4ADgAOAA4AAAAAAAAAAAAAAAAAAAAAAA4ADgAOAA4ADgAOAA4ADgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4AAAAOAA4ADgAOAA4ADgAAAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4ADgAOAA4AAAAAAAAAAAA=",
    zr = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",
    ce = typeof Uint8Array == "undefined" ? [] : new Uint8Array(256);
for (var ke = 0; ke < zr.length; ke++) ce[zr.charCodeAt(ke)] = ke;
var Fo = function (t) {
        var A = t.length * 0.75,
            e = t.length,
            r,
            n = 0,
            s,
            B,
            i,
            a;
        t[t.length - 1] === "=" && (A--, t[t.length - 2] === "=" && A--);
        var o =
                typeof ArrayBuffer != "undefined" &&
                typeof Uint8Array != "undefined" &&
                typeof Uint8Array.prototype.slice != "undefined"
                    ? new ArrayBuffer(A)
                    : new Array(A),
            c = Array.isArray(o) ? o : new Uint8Array(o);
        for (r = 0; r < e; r += 4)
            (s = ce[t.charCodeAt(r)]),
                (B = ce[t.charCodeAt(r + 1)]),
                (i = ce[t.charCodeAt(r + 2)]),
                (a = ce[t.charCodeAt(r + 3)]),
                (c[n++] = (s << 2) | (B >> 4)),
                (c[n++] = ((B & 15) << 4) | (i >> 2)),
                (c[n++] = ((i & 3) << 6) | (a & 63));
        return o;
    },
    po = function (t) {
        for (var A = t.length, e = [], r = 0; r < A; r += 2) e.push((t[r + 1] << 8) | t[r]);
        return e;
    },
    Eo = function (t) {
        for (var A = t.length, e = [], r = 0; r < A; r += 4)
            e.push((t[r + 3] << 24) | (t[r + 2] << 16) | (t[r + 1] << 8) | t[r]);
        return e;
    },
    NA = 5,
    Cr = 6 + 5,
    Kt = 2,
    Ho = Cr - NA,
    ls = 65536 >> NA,
    vo = 1 << NA,
    bt = vo - 1,
    Io = 1024 >> NA,
    mo = ls + Io,
    yo = mo,
    Lo = 32,
    Ko = yo + Lo,
    bo = 65536 >> Cr,
    xo = 1 << Ho,
    Do = xo - 1,
    $r = function (t, A, e) {
        return t.slice ? t.slice(A, e) : new Uint16Array(Array.prototype.slice.call(t, A, e));
    },
    So = function (t, A, e) {
        return t.slice ? t.slice(A, e) : new Uint32Array(Array.prototype.slice.call(t, A, e));
    },
    To = function (t, A) {
        var e = Fo(t),
            r = Array.isArray(e) ? Eo(e) : new Uint32Array(e),
            n = Array.isArray(e) ? po(e) : new Uint16Array(e),
            s = 24,
            B = $r(n, s / 2, r[4] / 2),
            i = r[5] === 2 ? $r(n, (s + r[4]) / 2) : So(r, Math.ceil((s + r[4]) / 4));
        return new Oo(r[0], r[1], r[2], r[3], B, i);
    },
    Oo = (function () {
        function t(A, e, r, n, s, B) {
            (this.initialValue = A),
                (this.errorValue = e),
                (this.highStart = r),
                (this.highValueIndex = n),
                (this.index = s),
                (this.data = B);
        }
        return (
            (t.prototype.get = function (A) {
                var e;
                if (A >= 0) {
                    if (A < 55296 || (A > 56319 && A <= 65535))
                        return (e = this.index[A >> NA]), (e = (e << Kt) + (A & bt)), this.data[e];
                    if (A <= 65535)
                        return (e = this.index[ls + ((A - 55296) >> NA)]), (e = (e << Kt) + (A & bt)), this.data[e];
                    if (A < this.highStart)
                        return (
                            (e = Ko - bo + (A >> Cr)),
                            (e = this.index[e]),
                            (e += (A >> NA) & Do),
                            (e = this.index[e]),
                            (e = (e << Kt) + (A & bt)),
                            this.data[e]
                        );
                    if (A <= 1114111) return this.data[this.highValueIndex];
                }
                return this.errorValue;
            }),
            t
        );
    })(),
    An = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",
    Mo = typeof Uint8Array == "undefined" ? [] : new Uint8Array(256);
for (var Pe = 0; Pe < An.length; Pe++) Mo[An.charCodeAt(Pe)] = Pe;
var Ro = 1,
    xt = 2,
    Dt = 3,
    en = 4,
    tn = 5,
    No = 7,
    rn = 8,
    St = 9,
    Tt = 10,
    nn = 11,
    sn = 12,
    Bn = 13,
    an = 14,
    Ot = 15,
    Go = function (t) {
        for (var A = [], e = 0, r = t.length; e < r; ) {
            var n = t.charCodeAt(e++);
            if (n >= 55296 && n <= 56319 && e < r) {
                var s = t.charCodeAt(e++);
                (s & 64512) === 56320 ? A.push(((n & 1023) << 10) + (s & 1023) + 65536) : (A.push(n), e--);
            } else A.push(n);
        }
        return A;
    },
    Vo = function () {
        for (var t = [], A = 0; A < arguments.length; A++) t[A] = arguments[A];
        if (String.fromCodePoint) return String.fromCodePoint.apply(String, t);
        var e = t.length;
        if (!e) return "";
        for (var r = [], n = -1, s = ""; ++n < e; ) {
            var B = t[n];
            B <= 65535 ? r.push(B) : ((B -= 65536), r.push((B >> 10) + 55296, (B % 1024) + 56320)),
                (n + 1 === e || r.length > 16384) && ((s += String.fromCharCode.apply(String, r)), (r.length = 0));
        }
        return s;
    },
    ko = To(Uo),
    AA = "×",
    Mt = "÷",
    Po = function (t) {
        return ko.get(t);
    },
    _o = function (t, A, e) {
        var r = e - 2,
            n = A[r],
            s = A[e - 1],
            B = A[e];
        if (s === xt && B === Dt) return AA;
        if (s === xt || s === Dt || s === en || B === xt || B === Dt || B === en) return Mt;
        if (
            (s === rn && [rn, St, nn, sn].indexOf(B) !== -1) ||
            ((s === nn || s === St) && (B === St || B === Tt)) ||
            ((s === sn || s === Tt) && B === Tt) ||
            B === Bn ||
            B === tn ||
            B === No ||
            s === Ro
        )
            return AA;
        if (s === Bn && B === an) {
            for (; n === tn; ) n = A[--r];
            if (n === an) return AA;
        }
        if (s === Ot && B === Ot) {
            for (var i = 0; n === Ot; ) i++, (n = A[--r]);
            if (i % 2 === 0) return AA;
        }
        return Mt;
    },
    Xo = function (t) {
        var A = Go(t),
            e = A.length,
            r = 0,
            n = 0,
            s = A.map(Po);
        return {
            next: function () {
                if (r >= e) return { done: !0, value: null };
                for (var B = AA; r < e && (B = _o(A, s, ++r)) === AA; );
                if (B !== AA || r === e) {
                    var i = Vo.apply(null, A.slice(n, r));
                    return (n = r), { value: i, done: !1 };
                }
                return { done: !0, value: null };
            },
        };
    },
    Jo = function (t) {
        for (var A = Xo(t), e = [], r; !(r = A.next()).done; ) r.value && e.push(r.value.slice());
        return e;
    },
    Yo = function (t) {
        var A = 123;
        if (t.createRange) {
            var e = t.createRange();
            if (e.getBoundingClientRect) {
                var r = t.createElement("boundtest");
                (r.style.height = A + "px"), (r.style.display = "block"), t.body.appendChild(r), e.selectNode(r);
                var n = e.getBoundingClientRect(),
                    s = Math.round(n.height);
                if ((t.body.removeChild(r), s === A)) return !0;
            }
        }
        return !1;
    },
    Wo = function (t) {
        var A = t.createElement("boundtest");
        (A.style.width = "50px"),
            (A.style.display = "block"),
            (A.style.fontSize = "12px"),
            (A.style.letterSpacing = "0px"),
            (A.style.wordSpacing = "0px"),
            t.body.appendChild(A);
        var e = t.createRange();
        A.innerHTML = typeof "".repeat == "function" ? "&#128104;".repeat(10) : "";
        var r = A.firstChild,
            n = gt(r.data).map(function (a) {
                return O(a);
            }),
            s = 0,
            B = {},
            i = n.every(function (a, o) {
                e.setStart(r, s), e.setEnd(r, s + a.length);
                var c = e.getBoundingClientRect();
                s += a.length;
                var l = c.x > B.x || c.y > B.y;
                return (B = c), o === 0 ? !0 : l;
            });
        return t.body.removeChild(A), i;
    },
    Zo = function () {
        return typeof new Image().crossOrigin != "undefined";
    },
    qo = function () {
        return typeof new XMLHttpRequest().responseType == "string";
    },
    jo = function (t) {
        var A = new Image(),
            e = t.createElement("canvas"),
            r = e.getContext("2d");
        if (!r) return !1;
        A.src = "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg'></svg>";
        try {
            r.drawImage(A, 0, 0), e.toDataURL();
        } catch (n) {
            return !1;
        }
        return !0;
    },
    on = function (t) {
        return t[0] === 0 && t[1] === 255 && t[2] === 0 && t[3] === 255;
    },
    zo = function (t) {
        var A = t.createElement("canvas"),
            e = 100;
        (A.width = e), (A.height = e);
        var r = A.getContext("2d");
        if (!r) return Promise.reject(!1);
        (r.fillStyle = "rgb(0, 255, 0)"), r.fillRect(0, 0, e, e);
        var n = new Image(),
            s = A.toDataURL();
        n.src = s;
        var B = sr(e, e, 0, 0, n);
        return (
            (r.fillStyle = "red"),
            r.fillRect(0, 0, e, e),
            cn(B)
                .then(function (i) {
                    r.drawImage(i, 0, 0);
                    var a = r.getImageData(0, 0, e, e).data;
                    (r.fillStyle = "red"), r.fillRect(0, 0, e, e);
                    var o = t.createElement("div");
                    return (
                        (o.style.backgroundImage = "url(" + s + ")"),
                        (o.style.height = e + "px"),
                        on(a) ? cn(sr(e, e, 0, 0, o)) : Promise.reject(!1)
                    );
                })
                .then(function (i) {
                    return r.drawImage(i, 0, 0), on(r.getImageData(0, 0, e, e).data);
                })
                .catch(function () {
                    return !1;
                })
        );
    },
    sr = function (t, A, e, r, n) {
        var s = "http://www.w3.org/2000/svg",
            B = document.createElementNS(s, "svg"),
            i = document.createElementNS(s, "foreignObject");
        return (
            B.setAttributeNS(null, "width", t.toString()),
            B.setAttributeNS(null, "height", A.toString()),
            i.setAttributeNS(null, "width", "100%"),
            i.setAttributeNS(null, "height", "100%"),
            i.setAttributeNS(null, "x", e.toString()),
            i.setAttributeNS(null, "y", r.toString()),
            i.setAttributeNS(null, "externalResourcesRequired", "true"),
            B.appendChild(i),
            i.appendChild(n),
            B
        );
    },
    cn = function (t) {
        return new Promise(function (A, e) {
            var r = new Image();
            (r.onload = function () {
                return A(r);
            }),
                (r.onerror = e),
                (r.src =
                    "data:image/svg+xml;charset=utf-8," + encodeURIComponent(new XMLSerializer().serializeToString(t)));
        });
    },
    k = {
        get SUPPORT_RANGE_BOUNDS() {
            var t = Yo(document);
            return Object.defineProperty(k, "SUPPORT_RANGE_BOUNDS", { value: t }), t;
        },
        get SUPPORT_WORD_BREAKING() {
            var t = k.SUPPORT_RANGE_BOUNDS && Wo(document);
            return Object.defineProperty(k, "SUPPORT_WORD_BREAKING", { value: t }), t;
        },
        get SUPPORT_SVG_DRAWING() {
            var t = jo(document);
            return Object.defineProperty(k, "SUPPORT_SVG_DRAWING", { value: t }), t;
        },
        get SUPPORT_FOREIGNOBJECT_DRAWING() {
            var t =
                typeof Array.from == "function" && typeof window.fetch == "function"
                    ? zo(document)
                    : Promise.resolve(!1);
            return Object.defineProperty(k, "SUPPORT_FOREIGNOBJECT_DRAWING", { value: t }), t;
        },
        get SUPPORT_CORS_IMAGES() {
            var t = Zo();
            return Object.defineProperty(k, "SUPPORT_CORS_IMAGES", { value: t }), t;
        },
        get SUPPORT_RESPONSE_TYPE() {
            var t = qo();
            return Object.defineProperty(k, "SUPPORT_RESPONSE_TYPE", { value: t }), t;
        },
        get SUPPORT_CORS_XHR() {
            var t = "withCredentials" in new XMLHttpRequest();
            return Object.defineProperty(k, "SUPPORT_CORS_XHR", { value: t }), t;
        },
        get SUPPORT_NATIVE_TEXT_SEGMENTATION() {
            var t = !!(typeof Intl != "undefined" && Intl.Segmenter);
            return Object.defineProperty(k, "SUPPORT_NATIVE_TEXT_SEGMENTATION", { value: t }), t;
        },
    },
    we = (function () {
        function t(A, e) {
            (this.text = A), (this.bounds = e);
        }
        return t;
    })(),
    $o = function (t, A, e, r) {
        var n = tc(A, e),
            s = [],
            B = 0;
        return (
            n.forEach(function (i) {
                if (e.textDecorationLine.length || i.trim().length > 0)
                    if (k.SUPPORT_RANGE_BOUNDS) {
                        var a = ln(r, B, i.length).getClientRects();
                        if (a.length > 1) {
                            var o = hr(i),
                                c = 0;
                            o.forEach(function (g) {
                                s.push(new we(g, fA.fromDOMRectList(t, ln(r, c + B, g.length).getClientRects()))),
                                    (c += g.length);
                            });
                        } else s.push(new we(i, fA.fromDOMRectList(t, a)));
                    } else {
                        var l = r.splitText(i.length);
                        s.push(new we(i, Ac(t, r))), (r = l);
                    }
                else k.SUPPORT_RANGE_BOUNDS || (r = r.splitText(i.length));
                B += i.length;
            }),
            s
        );
    },
    Ac = function (t, A) {
        var e = A.ownerDocument;
        if (e) {
            var r = e.createElement("html2canvaswrapper");
            r.appendChild(A.cloneNode(!0));
            var n = A.parentNode;
            if (n) {
                n.replaceChild(r, A);
                var s = lt(t, r);
                return r.firstChild && n.replaceChild(r.firstChild, r), s;
            }
        }
        return fA.EMPTY;
    },
    ln = function (t, A, e) {
        var r = t.ownerDocument;
        if (!r) throw new Error("Node has no owner document");
        var n = r.createRange();
        return n.setStart(t, A), n.setEnd(t, A + e), n;
    },
    hr = function (t) {
        if (k.SUPPORT_NATIVE_TEXT_SEGMENTATION) {
            var A = new Intl.Segmenter(void 0, { granularity: "grapheme" });
            return Array.from(A.segment(t)).map(function (e) {
                return e.segment;
            });
        }
        return Jo(t);
    },
    ec = function (t, A) {
        if (k.SUPPORT_NATIVE_TEXT_SEGMENTATION) {
            var e = new Intl.Segmenter(void 0, { granularity: "word" });
            return Array.from(e.segment(t)).map(function (r) {
                return r.segment;
            });
        }
        return nc(t, A);
    },
    tc = function (t, A) {
        return A.letterSpacing !== 0 ? hr(t) : ec(t, A);
    },
    rc = [32, 160, 4961, 65792, 65793, 4153, 4241],
    nc = function (t, A) {
        for (
            var e = KB(t, {
                    lineBreak: A.lineBreak,
                    wordBreak: A.overflowWrap === "break-word" ? "break-word" : A.wordBreak,
                }),
                r = [],
                n,
                s = function () {
                    if (n.value) {
                        var B = n.value.slice(),
                            i = gt(B),
                            a = "";
                        i.forEach(function (o) {
                            rc.indexOf(o) === -1 ? (a += O(o)) : (a.length && r.push(a), r.push(O(o)), (a = ""));
                        }),
                            a.length && r.push(a);
                    }
                };
            !(n = e.next()).done;

        )
            s();
        return r;
    },
    sc = (function () {
        function t(A, e, r) {
            (this.text = Bc(e.data, r.textTransform)), (this.textBounds = $o(A, this.text, r, e));
        }
        return t;
    })(),
    Bc = function (t, A) {
        switch (A) {
            case 1:
                return t.toLowerCase();
            case 3:
                return t.replace(ic, ac);
            case 2:
                return t.toUpperCase();
            default:
                return t;
        }
    },
    ic = /(^|\s|:|-|\(|\))([a-z])/g,
    ac = function (t, A, e) {
        return t.length > 0 ? A + e.toUpperCase() : t;
    },
    gs = (function (t) {
        sA(A, t);
        function A(e, r) {
            var n = t.call(this, e, r) || this;
            return (
                (n.src = r.currentSrc || r.src),
                (n.intrinsicWidth = r.naturalWidth),
                (n.intrinsicHeight = r.naturalHeight),
                n.context.cache.addImage(n.src),
                n
            );
        }
        return A;
    })(cA),
    us = (function (t) {
        sA(A, t);
        function A(e, r) {
            var n = t.call(this, e, r) || this;
            return (n.canvas = r), (n.intrinsicWidth = r.width), (n.intrinsicHeight = r.height), n;
        }
        return A;
    })(cA),
    Qs = (function (t) {
        sA(A, t);
        function A(e, r) {
            var n = t.call(this, e, r) || this,
                s = new XMLSerializer(),
                B = lt(e, r);
            return (
                r.setAttribute("width", B.width + "px"),
                r.setAttribute("height", B.height + "px"),
                (n.svg = "data:image/svg+xml," + encodeURIComponent(s.serializeToString(r))),
                (n.intrinsicWidth = r.width.baseVal.value),
                (n.intrinsicHeight = r.height.baseVal.value),
                n.context.cache.addImage(n.svg),
                n
            );
        }
        return A;
    })(cA),
    ws = (function (t) {
        sA(A, t);
        function A(e, r) {
            var n = t.call(this, e, r) || this;
            return (n.value = r.value), n;
        }
        return A;
    })(cA),
    Br = (function (t) {
        sA(A, t);
        function A(e, r) {
            var n = t.call(this, e, r) || this;
            return (n.start = r.start), (n.reversed = typeof r.reversed == "boolean" && r.reversed === !0), n;
        }
        return A;
    })(cA),
    oc = [{ type: 15, flags: 0, unit: "px", number: 3 }],
    cc = [{ type: 16, flags: 0, number: 50 }],
    lc = function (t) {
        return t.width > t.height
            ? new fA(t.left + (t.width - t.height) / 2, t.top, t.height, t.height)
            : t.width < t.height
            ? new fA(t.left, t.top + (t.height - t.width) / 2, t.width, t.width)
            : t;
    },
    gc = function (t) {
        var A = t.type === uc ? new Array(t.value.length + 1).join("•") : t.value;
        return A.length === 0 ? t.placeholder || "" : A;
    },
    rt = "checkbox",
    nt = "radio",
    uc = "password",
    gn = 707406591,
    Ur = (function (t) {
        sA(A, t);
        function A(e, r) {
            var n = t.call(this, e, r) || this;
            switch (
                ((n.type = r.type.toLowerCase()),
                (n.checked = r.checked),
                (n.value = gc(r)),
                (n.type === rt || n.type === nt) &&
                    ((n.styles.backgroundColor = 3739148031),
                    (n.styles.borderTopColor =
                        n.styles.borderRightColor =
                        n.styles.borderBottomColor =
                        n.styles.borderLeftColor =
                            2779096575),
                    (n.styles.borderTopWidth =
                        n.styles.borderRightWidth =
                        n.styles.borderBottomWidth =
                        n.styles.borderLeftWidth =
                            1),
                    (n.styles.borderTopStyle =
                        n.styles.borderRightStyle =
                        n.styles.borderBottomStyle =
                        n.styles.borderLeftStyle =
                            1),
                    (n.styles.backgroundClip = [0]),
                    (n.styles.backgroundOrigin = [0]),
                    (n.bounds = lc(n.bounds))),
                n.type)
            ) {
                case rt:
                    n.styles.borderTopRightRadius =
                        n.styles.borderTopLeftRadius =
                        n.styles.borderBottomRightRadius =
                        n.styles.borderBottomLeftRadius =
                            oc;
                    break;
                case nt:
                    n.styles.borderTopRightRadius =
                        n.styles.borderTopLeftRadius =
                        n.styles.borderBottomRightRadius =
                        n.styles.borderBottomLeftRadius =
                            cc;
                    break;
            }
            return n;
        }
        return A;
    })(cA),
    fs = (function (t) {
        sA(A, t);
        function A(e, r) {
            var n = t.call(this, e, r) || this,
                s = r.options[r.selectedIndex || 0];
            return (n.value = (s && s.text) || ""), n;
        }
        return A;
    })(cA),
    Cs = (function (t) {
        sA(A, t);
        function A(e, r) {
            var n = t.call(this, e, r) || this;
            return (n.value = r.value), n;
        }
        return A;
    })(cA),
    hs = (function (t) {
        sA(A, t);
        function A(e, r) {
            var n = t.call(this, e, r) || this;
            (n.src = r.src),
                (n.width = parseInt(r.width, 10) || 0),
                (n.height = parseInt(r.height, 10) || 0),
                (n.backgroundColor = n.styles.backgroundColor);
            try {
                if (r.contentWindow && r.contentWindow.document && r.contentWindow.document.documentElement) {
                    n.tree = Fs(e, r.contentWindow.document.documentElement);
                    var s = r.contentWindow.document.documentElement
                            ? ue(e, getComputedStyle(r.contentWindow.document.documentElement).backgroundColor)
                            : wA.TRANSPARENT,
                        B = r.contentWindow.document.body
                            ? ue(e, getComputedStyle(r.contentWindow.document.body).backgroundColor)
                            : wA.TRANSPARENT;
                    n.backgroundColor = mA(s) ? (mA(B) ? n.styles.backgroundColor : B) : s;
                }
            } catch (i) {}
            return n;
        }
        return A;
    })(cA),
    Qc = ["OL", "UL", "MENU"],
    je = function (t, A, e, r) {
        for (var n = A.firstChild, s = void 0; n; n = s)
            if (((s = n.nextSibling), ds(n) && n.data.trim().length > 0)) e.textNodes.push(new sc(t, n, e.styles));
            else if (ZA(n))
                if (vs(n) && n.assignedNodes)
                    n.assignedNodes().forEach(function (i) {
                        return je(t, i, e, r);
                    });
                else {
                    var B = Us(t, n);
                    B.styles.isVisible() &&
                        (wc(n, B, r) ? (B.flags |= 4) : fc(B.styles) && (B.flags |= 2),
                        Qc.indexOf(n.tagName) !== -1 && (B.flags |= 8),
                        e.elements.push(B),
                        n.slot,
                        n.shadowRoot ? je(t, n.shadowRoot, B, r) : !st(n) && !ps(n) && !Bt(n) && je(t, n, B, r));
                }
    },
    Us = function (t, A) {
        return ar(A)
            ? new gs(t, A)
            : Es(A)
            ? new us(t, A)
            : ps(A)
            ? new Qs(t, A)
            : Cc(A)
            ? new ws(t, A)
            : hc(A)
            ? new Br(t, A)
            : Uc(A)
            ? new Ur(t, A)
            : Bt(A)
            ? new fs(t, A)
            : st(A)
            ? new Cs(t, A)
            : Hs(A)
            ? new hs(t, A)
            : new cA(t, A);
    },
    Fs = function (t, A) {
        var e = Us(t, A);
        return (e.flags |= 4), je(t, A, e, e), e;
    },
    wc = function (t, A, e) {
        return (
            A.styles.isPositionedWithZIndex() ||
            A.styles.opacity < 1 ||
            A.styles.isTransformed() ||
            (Fr(t) && e.styles.isTransparent())
        );
    },
    fc = function (t) {
        return t.isPositioned() || t.isFloating();
    },
    ds = function (t) {
        return t.nodeType === Node.TEXT_NODE;
    },
    ZA = function (t) {
        return t.nodeType === Node.ELEMENT_NODE;
    },
    ir = function (t) {
        return ZA(t) && typeof t.style != "undefined" && !ze(t);
    },
    ze = function (t) {
        return typeof t.className == "object";
    },
    Cc = function (t) {
        return t.tagName === "LI";
    },
    hc = function (t) {
        return t.tagName === "OL";
    },
    Uc = function (t) {
        return t.tagName === "INPUT";
    },
    Fc = function (t) {
        return t.tagName === "HTML";
    },
    ps = function (t) {
        return t.tagName === "svg";
    },
    Fr = function (t) {
        return t.tagName === "BODY";
    },
    Es = function (t) {
        return t.tagName === "CANVAS";
    },
    un = function (t) {
        return t.tagName === "VIDEO";
    },
    ar = function (t) {
        return t.tagName === "IMG";
    },
    Hs = function (t) {
        return t.tagName === "IFRAME";
    },
    Qn = function (t) {
        return t.tagName === "STYLE";
    },
    dc = function (t) {
        return t.tagName === "SCRIPT";
    },
    st = function (t) {
        return t.tagName === "TEXTAREA";
    },
    Bt = function (t) {
        return t.tagName === "SELECT";
    },
    vs = function (t) {
        return t.tagName === "SLOT";
    },
    wn = function (t) {
        return t.tagName.indexOf("-") > 0;
    },
    pc = (function () {
        function t() {
            this.counters = {};
        }
        return (
            (t.prototype.getCounterValue = function (A) {
                var e = this.counters[A];
                return e && e.length ? e[e.length - 1] : 1;
            }),
            (t.prototype.getCounterValues = function (A) {
                var e = this.counters[A];
                return e || [];
            }),
            (t.prototype.pop = function (A) {
                var e = this;
                A.forEach(function (r) {
                    return e.counters[r].pop();
                });
            }),
            (t.prototype.parse = function (A) {
                var e = this,
                    r = A.counterIncrement,
                    n = A.counterReset,
                    s = !0;
                r !== null &&
                    r.forEach(function (i) {
                        var a = e.counters[i.counter];
                        a &&
                            i.increment !== 0 &&
                            ((s = !1), a.length || a.push(1), (a[Math.max(0, a.length - 1)] += i.increment));
                    });
                var B = [];
                return (
                    s &&
                        n.forEach(function (i) {
                            var a = e.counters[i.counter];
                            B.push(i.counter), a || (a = e.counters[i.counter] = []), a.push(i.reset);
                        }),
                    B
                );
            }),
            t
        );
    })(),
    fn = {
        integers: [1e3, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1],
        values: ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"],
    },
    Cn = {
        integers: [
            9e3, 8e3, 7e3, 6e3, 5e3, 4e3, 3e3, 2e3, 1e3, 900, 800, 700, 600, 500, 400, 300, 200, 100, 90, 80, 70, 60,
            50, 40, 30, 20, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1,
        ],
        values: [
            "Ք",
            "Փ",
            "Ւ",
            "Ց",
            "Ր",
            "Տ",
            "Վ",
            "Ս",
            "Ռ",
            "Ջ",
            "Պ",
            "Չ",
            "Ո",
            "Շ",
            "Ն",
            "Յ",
            "Մ",
            "Ճ",
            "Ղ",
            "Ձ",
            "Հ",
            "Կ",
            "Ծ",
            "Խ",
            "Լ",
            "Ի",
            "Ժ",
            "Թ",
            "Ը",
            "Է",
            "Զ",
            "Ե",
            "Դ",
            "Գ",
            "Բ",
            "Ա",
        ],
    },
    Ec = {
        integers: [
            1e4, 9e3, 8e3, 7e3, 6e3, 5e3, 4e3, 3e3, 2e3, 1e3, 400, 300, 200, 100, 90, 80, 70, 60, 50, 40, 30, 20, 19,
            18, 17, 16, 15, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1,
        ],
        values: [
            "י׳",
            "ט׳",
            "ח׳",
            "ז׳",
            "ו׳",
            "ה׳",
            "ד׳",
            "ג׳",
            "ב׳",
            "א׳",
            "ת",
            "ש",
            "ר",
            "ק",
            "צ",
            "פ",
            "ע",
            "ס",
            "נ",
            "מ",
            "ל",
            "כ",
            "יט",
            "יח",
            "יז",
            "טז",
            "טו",
            "י",
            "ט",
            "ח",
            "ז",
            "ו",
            "ה",
            "ד",
            "ג",
            "ב",
            "א",
        ],
    },
    Hc = {
        integers: [
            1e4, 9e3, 8e3, 7e3, 6e3, 5e3, 4e3, 3e3, 2e3, 1e3, 900, 800, 700, 600, 500, 400, 300, 200, 100, 90, 80, 70,
            60, 50, 40, 30, 20, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1,
        ],
        values: [
            "ჵ",
            "ჰ",
            "ჯ",
            "ჴ",
            "ხ",
            "ჭ",
            "წ",
            "ძ",
            "ც",
            "ჩ",
            "შ",
            "ყ",
            "ღ",
            "ქ",
            "ფ",
            "ჳ",
            "ტ",
            "ს",
            "რ",
            "ჟ",
            "პ",
            "ო",
            "ჲ",
            "ნ",
            "მ",
            "ლ",
            "კ",
            "ი",
            "თ",
            "ჱ",
            "ზ",
            "ვ",
            "ე",
            "დ",
            "გ",
            "ბ",
            "ა",
        ],
    },
    _A = function (t, A, e, r, n, s) {
        return t < A || t > e
            ? Ue(t, n, s.length > 0)
            : r.integers.reduce(function (B, i, a) {
                  for (; t >= i; ) (t -= i), (B += r.values[a]);
                  return B;
              }, "") + s;
    },
    Is = function (t, A, e, r) {
        var n = "";
        do e || t--, (n = r(t) + n), (t /= A);
        while (t * A >= A);
        return n;
    },
    T = function (t, A, e, r, n) {
        var s = e - A + 1;
        return (
            (t < 0 ? "-" : "") +
            (Is(Math.abs(t), s, r, function (B) {
                return O(Math.floor(B % s) + A);
            }) +
                n)
        );
    },
    SA = function (t, A, e) {
        e === void 0 && (e = ". ");
        var r = A.length;
        return (
            Is(Math.abs(t), r, !1, function (n) {
                return A[Math.floor(n % r)];
            }) + e
        );
    },
    YA = 1 << 0,
    FA = 1 << 1,
    dA = 1 << 2,
    le = 1 << 3,
    QA = function (t, A, e, r, n, s) {
        if (t < -9999 || t > 9999) return Ue(t, 4, n.length > 0);
        var B = Math.abs(t),
            i = n;
        if (B === 0) return A[0] + i;
        for (var a = 0; B > 0 && a <= 4; a++) {
            var o = B % 10;
            o === 0 && N(s, YA) && i !== ""
                ? (i = A[o] + i)
                : o > 1 ||
                  (o === 1 && a === 0) ||
                  (o === 1 && a === 1 && N(s, FA)) ||
                  (o === 1 && a === 1 && N(s, dA) && t > 100) ||
                  (o === 1 && a > 1 && N(s, le))
                ? (i = A[o] + (a > 0 ? e[a - 1] : "") + i)
                : o === 1 && a > 0 && (i = e[a - 1] + i),
                (B = Math.floor(B / 10));
        }
        return (t < 0 ? r : "") + i;
    },
    hn = "十百千萬",
    Un = "拾佰仟萬",
    Fn = "マイナス",
    Rt = "마이너스",
    Ue = function (t, A, e) {
        var r = e ? ". " : "",
            n = e ? "、" : "",
            s = e ? ", " : "",
            B = e ? " " : "";
        switch (A) {
            case 0:
                return "•" + B;
            case 1:
                return "◦" + B;
            case 2:
                return "◾" + B;
            case 5:
                var i = T(t, 48, 57, !0, r);
                return i.length < 4 ? "0" + i : i;
            case 4:
                return SA(t, "〇一二三四五六七八九", n);
            case 6:
                return _A(t, 1, 3999, fn, 3, r).toLowerCase();
            case 7:
                return _A(t, 1, 3999, fn, 3, r);
            case 8:
                return T(t, 945, 969, !1, r);
            case 9:
                return T(t, 97, 122, !1, r);
            case 10:
                return T(t, 65, 90, !1, r);
            case 11:
                return T(t, 1632, 1641, !0, r);
            case 12:
            case 49:
                return _A(t, 1, 9999, Cn, 3, r);
            case 35:
                return _A(t, 1, 9999, Cn, 3, r).toLowerCase();
            case 13:
                return T(t, 2534, 2543, !0, r);
            case 14:
            case 30:
                return T(t, 6112, 6121, !0, r);
            case 15:
                return SA(t, "子丑寅卯辰巳午未申酉戌亥", n);
            case 16:
                return SA(t, "甲乙丙丁戊己庚辛壬癸", n);
            case 17:
            case 48:
                return QA(t, "零一二三四五六七八九", hn, "負", n, FA | dA | le);
            case 47:
                return QA(t, "零壹貳參肆伍陸柒捌玖", Un, "負", n, YA | FA | dA | le);
            case 42:
                return QA(t, "零一二三四五六七八九", hn, "负", n, FA | dA | le);
            case 41:
                return QA(t, "零壹贰叁肆伍陆柒捌玖", Un, "负", n, YA | FA | dA | le);
            case 26:
                return QA(t, "〇一二三四五六七八九", "十百千万", Fn, n, 0);
            case 25:
                return QA(t, "零壱弐参四伍六七八九", "拾百千万", Fn, n, YA | FA | dA);
            case 31:
                return QA(t, "영일이삼사오육칠팔구", "십백천만", Rt, s, YA | FA | dA);
            case 33:
                return QA(t, "零一二三四五六七八九", "十百千萬", Rt, s, 0);
            case 32:
                return QA(t, "零壹貳參四五六七八九", "拾百千", Rt, s, YA | FA | dA);
            case 18:
                return T(t, 2406, 2415, !0, r);
            case 20:
                return _A(t, 1, 19999, Hc, 3, r);
            case 21:
                return T(t, 2790, 2799, !0, r);
            case 22:
                return T(t, 2662, 2671, !0, r);
            case 22:
                return _A(t, 1, 10999, Ec, 3, r);
            case 23:
                return SA(
                    t,
                    "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわゐゑをん"
                );
            case 24:
                return SA(
                    t,
                    "いろはにほへとちりぬるをわかよたれそつねならむうゐのおくやまけふこえてあさきゆめみしゑひもせす"
                );
            case 27:
                return T(t, 3302, 3311, !0, r);
            case 28:
                return SA(
                    t,
                    "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヰヱヲン",
                    n
                );
            case 29:
                return SA(
                    t,
                    "イロハニホヘトチリヌルヲワカヨタレソツネナラムウヰノオクヤマケフコエテアサキユメミシヱヒモセス",
                    n
                );
            case 34:
                return T(t, 3792, 3801, !0, r);
            case 37:
                return T(t, 6160, 6169, !0, r);
            case 38:
                return T(t, 4160, 4169, !0, r);
            case 39:
                return T(t, 2918, 2927, !0, r);
            case 40:
                return T(t, 1776, 1785, !0, r);
            case 43:
                return T(t, 3046, 3055, !0, r);
            case 44:
                return T(t, 3174, 3183, !0, r);
            case 45:
                return T(t, 3664, 3673, !0, r);
            case 46:
                return T(t, 3872, 3881, !0, r);
            case 3:
            default:
                return T(t, 48, 57, !0, r);
        }
    },
    ms = "data-html2canvas-ignore",
    dn = (function () {
        function t(A, e, r) {
            if (
                ((this.context = A),
                (this.options = r),
                (this.scrolledElements = []),
                (this.referenceElement = e),
                (this.counters = new pc()),
                (this.quoteDepth = 0),
                !e.ownerDocument)
            )
                throw new Error("Cloned element does not have an owner document");
            this.documentElement = this.cloneNode(e.ownerDocument.documentElement, !1);
        }
        return (
            (t.prototype.toIFrame = function (A, e) {
                var r = this,
                    n = vc(A, e);
                if (!n.contentWindow) return Promise.reject("Unable to find iframe window");
                var s = A.defaultView.pageXOffset,
                    B = A.defaultView.pageYOffset,
                    i = n.contentWindow,
                    a = i.document,
                    o = yc(n).then(function () {
                        return J(r, void 0, void 0, function () {
                            var c, l;
                            return _(this, function (g) {
                                switch (g.label) {
                                    case 0:
                                        return (
                                            this.scrolledElements.forEach(xc),
                                            i &&
                                                (i.scrollTo(e.left, e.top),
                                                /(iPad|iPhone|iPod)/g.test(navigator.userAgent) &&
                                                    (i.scrollY !== e.top || i.scrollX !== e.left) &&
                                                    (this.context.logger.warn(
                                                        "Unable to restore scroll position for cloned document"
                                                    ),
                                                    (this.context.windowBounds = this.context.windowBounds.add(
                                                        i.scrollX - e.left,
                                                        i.scrollY - e.top,
                                                        0,
                                                        0
                                                    )))),
                                            (c = this.options.onclone),
                                            (l = this.clonedReferenceElement),
                                            typeof l == "undefined"
                                                ? [
                                                      2,
                                                      Promise.reject(
                                                          "Error finding the " +
                                                              this.referenceElement.nodeName +
                                                              " in the cloned document"
                                                      ),
                                                  ]
                                                : a.fonts && a.fonts.ready
                                                ? [4, a.fonts.ready]
                                                : [3, 2]
                                        );
                                    case 1:
                                        g.sent(), (g.label = 2);
                                    case 2:
                                        return /(AppleWebKit)/g.test(navigator.userAgent) ? [4, mc(a)] : [3, 4];
                                    case 3:
                                        g.sent(), (g.label = 4);
                                    case 4:
                                        return typeof c == "function"
                                            ? [
                                                  2,
                                                  Promise.resolve()
                                                      .then(function () {
                                                          return c(a, l);
                                                      })
                                                      .then(function () {
                                                          return n;
                                                      }),
                                              ]
                                            : [2, n];
                                }
                            });
                        });
                    });
                return (
                    a.open(),
                    a.write(Kc(document.doctype) + "<html></html>"),
                    bc(this.referenceElement.ownerDocument, s, B),
                    a.replaceChild(a.adoptNode(this.documentElement), a.documentElement),
                    a.close(),
                    o
                );
            }),
            (t.prototype.createElementClone = function (A) {
                if (nr(A, 2)) debugger;
                if (Es(A)) return this.createCanvasClone(A);
                if (un(A)) return this.createVideoClone(A);
                if (Qn(A)) return this.createStyleClone(A);
                var e = A.cloneNode(!1);
                return (
                    ar(e) &&
                        (ar(A) && A.currentSrc && A.currentSrc !== A.src && ((e.src = A.currentSrc), (e.srcset = "")),
                        e.loading === "lazy" && (e.loading = "eager")),
                    wn(e) ? this.createCustomElementClone(e) : e
                );
            }),
            (t.prototype.createCustomElementClone = function (A) {
                var e = document.createElement("html2canvascustomelement");
                return Nt(A.style, e), e;
            }),
            (t.prototype.createStyleClone = function (A) {
                try {
                    var e = A.sheet;
                    if (e && e.cssRules) {
                        var r = [].slice.call(e.cssRules, 0).reduce(function (s, B) {
                                return B && typeof B.cssText == "string" ? s + B.cssText : s;
                            }, ""),
                            n = A.cloneNode(!1);
                        return (n.textContent = r), n;
                    }
                } catch (s) {
                    if (
                        (this.context.logger.error("Unable to access cssRules property", s), s.name !== "SecurityError")
                    )
                        throw s;
                }
                return A.cloneNode(!1);
            }),
            (t.prototype.createCanvasClone = function (A) {
                var e;
                if (this.options.inlineImages && A.ownerDocument) {
                    var r = A.ownerDocument.createElement("img");
                    try {
                        return (r.src = A.toDataURL()), r;
                    } catch (o) {
                        this.context.logger.info("Unable to inline canvas contents, canvas is tainted", A);
                    }
                }
                var n = A.cloneNode(!1);
                try {
                    (n.width = A.width), (n.height = A.height);
                    var s = A.getContext("2d"),
                        B = n.getContext("2d");
                    if (B)
                        if (!this.options.allowTaint && s)
                            B.putImageData(s.getImageData(0, 0, A.width, A.height), 0, 0);
                        else {
                            var i = (e = A.getContext("webgl2")) !== null && e !== void 0 ? e : A.getContext("webgl");
                            if (i) {
                                var a = i.getContextAttributes();
                                (a == null ? void 0 : a.preserveDrawingBuffer) === !1 &&
                                    this.context.logger.warn(
                                        "Unable to clone WebGL context as it has preserveDrawingBuffer=false",
                                        A
                                    );
                            }
                            B.drawImage(A, 0, 0);
                        }
                    return n;
                } catch (o) {
                    this.context.logger.info("Unable to clone canvas as it is tainted", A);
                }
                return n;
            }),
            (t.prototype.createVideoClone = function (A) {
                var e = A.ownerDocument.createElement("canvas");
                (e.width = A.offsetWidth), (e.height = A.offsetHeight);
                var r = e.getContext("2d");
                try {
                    return (
                        r &&
                            (r.drawImage(A, 0, 0, e.width, e.height),
                            this.options.allowTaint || r.getImageData(0, 0, e.width, e.height)),
                        e
                    );
                } catch (s) {
                    this.context.logger.info("Unable to clone video as it is tainted", A);
                }
                var n = A.ownerDocument.createElement("canvas");
                return (n.width = A.offsetWidth), (n.height = A.offsetHeight), n;
            }),
            (t.prototype.appendChildNode = function (A, e, r) {
                (!ZA(e) ||
                    (!dc(e) &&
                        !e.hasAttribute(ms) &&
                        (typeof this.options.ignoreElements != "function" || !this.options.ignoreElements(e)))) &&
                    (!this.options.copyStyles || !ZA(e) || !Qn(e)) &&
                    A.appendChild(this.cloneNode(e, r));
            }),
            (t.prototype.cloneChildNodes = function (A, e, r) {
                for (var n = this, s = A.shadowRoot ? A.shadowRoot.firstChild : A.firstChild; s; s = s.nextSibling)
                    if (ZA(s) && vs(s) && typeof s.assignedNodes == "function") {
                        var B = s.assignedNodes();
                        B.length &&
                            B.forEach(function (i) {
                                return n.appendChildNode(e, i, r);
                            });
                    } else this.appendChildNode(e, s, r);
            }),
            (t.prototype.cloneNode = function (A, e) {
                if (ds(A)) return document.createTextNode(A.data);
                if (!A.ownerDocument) return A.cloneNode(!1);
                var r = A.ownerDocument.defaultView;
                if (r && ZA(A) && (ir(A) || ze(A))) {
                    var n = this.createElementClone(A);
                    n.style.transitionProperty = "none";
                    var s = r.getComputedStyle(A),
                        B = r.getComputedStyle(A, ":before"),
                        i = r.getComputedStyle(A, ":after");
                    this.referenceElement === A && ir(n) && (this.clonedReferenceElement = n), Fr(n) && Tc(n);
                    var a = this.counters.parse(new jr(this.context, s)),
                        o = this.resolvePseudoContent(A, n, B, fe.BEFORE);
                    wn(A) && (e = !0), un(A) || this.cloneChildNodes(A, n, e), o && n.insertBefore(o, n.firstChild);
                    var c = this.resolvePseudoContent(A, n, i, fe.AFTER);
                    return (
                        c && n.appendChild(c),
                        this.counters.pop(a),
                        ((s && (this.options.copyStyles || ze(A)) && !Hs(A)) || e) && Nt(s, n),
                        (A.scrollTop !== 0 || A.scrollLeft !== 0) &&
                            this.scrolledElements.push([n, A.scrollLeft, A.scrollTop]),
                        (st(A) || Bt(A)) && (st(n) || Bt(n)) && (n.value = A.value),
                        n
                    );
                }
                return A.cloneNode(!1);
            }),
            (t.prototype.resolvePseudoContent = function (A, e, r, n) {
                var s = this;
                if (r) {
                    var B = r.content,
                        i = e.ownerDocument;
                    if (!(!i || !B || B === "none" || B === "-moz-alt-content" || r.display === "none")) {
                        this.counters.parse(new jr(this.context, r));
                        var a = new fo(this.context, r),
                            o = i.createElement("html2canvaspseudoelement");
                        Nt(r, o),
                            a.content.forEach(function (l) {
                                if (l.type === 0) o.appendChild(i.createTextNode(l.value));
                                else if (l.type === 22) {
                                    var g = i.createElement("img");
                                    (g.src = l.value), (g.style.opacity = "1"), o.appendChild(g);
                                } else if (l.type === 18) {
                                    if (l.name === "attr") {
                                        var w = l.values.filter(x);
                                        w.length && o.appendChild(i.createTextNode(A.getAttribute(w[0].value) || ""));
                                    } else if (l.name === "counter") {
                                        var Q = l.values.filter(jA),
                                            f = Q[0],
                                            H = Q[1];
                                        if (f && x(f)) {
                                            var d = s.counters.getCounterValue(f.value),
                                                F = H && x(H) ? rr.parse(s.context, H.value) : 3;
                                            o.appendChild(i.createTextNode(Ue(d, F, !1)));
                                        }
                                    } else if (l.name === "counters") {
                                        var L = l.values.filter(jA),
                                            f = L[0],
                                            v = L[1],
                                            H = L[2];
                                        if (f && x(f)) {
                                            var p = s.counters.getCounterValues(f.value),
                                                h = H && x(H) ? rr.parse(s.context, H.value) : 3,
                                                m = v && v.type === 0 ? v.value : "",
                                                y = p
                                                    .map(function (Y) {
                                                        return Ue(Y, h, !1);
                                                    })
                                                    .join(m);
                                            o.appendChild(i.createTextNode(y));
                                        }
                                    }
                                } else if (l.type === 20)
                                    switch (l.value) {
                                        case "open-quote":
                                            o.appendChild(i.createTextNode(qr(a.quotes, s.quoteDepth++, !0)));
                                            break;
                                        case "close-quote":
                                            o.appendChild(i.createTextNode(qr(a.quotes, --s.quoteDepth, !1)));
                                            break;
                                        default:
                                            o.appendChild(i.createTextNode(l.value));
                                    }
                            }),
                            (o.className = or + " " + cr);
                        var c = n === fe.BEFORE ? " " + or : " " + cr;
                        return ze(e) ? (e.className.baseValue += c) : (e.className += c), o;
                    }
                }
            }),
            (t.destroy = function (A) {
                return A.parentNode ? (A.parentNode.removeChild(A), !0) : !1;
            }),
            t
        );
    })(),
    fe;
(function (t) {
    (t[(t.BEFORE = 0)] = "BEFORE"), (t[(t.AFTER = 1)] = "AFTER");
})(fe || (fe = {}));
var vc = function (t, A) {
        var e = t.createElement("iframe");
        return (
            (e.className = "html2canvas-container"),
            (e.style.visibility = "hidden"),
            (e.style.position = "fixed"),
            (e.style.left = "-10000px"),
            (e.style.top = "0px"),
            (e.style.border = "0"),
            (e.width = A.width.toString()),
            (e.height = A.height.toString()),
            (e.scrolling = "no"),
            e.setAttribute(ms, "true"),
            t.body.appendChild(e),
            e
        );
    },
    Ic = function (t) {
        return new Promise(function (A) {
            if (t.complete) {
                A();
                return;
            }
            if (!t.src) {
                A();
                return;
            }
            (t.onload = A), (t.onerror = A);
        });
    },
    mc = function (t) {
        return Promise.all([].slice.call(t.images, 0).map(Ic));
    },
    yc = function (t) {
        return new Promise(function (A, e) {
            var r = t.contentWindow;
            if (!r) return e("No window assigned for iframe");
            var n = r.document;
            r.onload = t.onload = function () {
                r.onload = t.onload = null;
                var s = setInterval(function () {
                    n.body.childNodes.length > 0 && n.readyState === "complete" && (clearInterval(s), A(t));
                }, 50);
            };
        });
    },
    Lc = ["all", "d", "content"],
    Nt = function (t, A) {
        for (var e = t.length - 1; e >= 0; e--) {
            var r = t.item(e);
            Lc.indexOf(r) === -1 && A.style.setProperty(r, t.getPropertyValue(r));
        }
        return A;
    },
    Kc = function (t) {
        var A = "";
        return (
            t &&
                ((A += "<!DOCTYPE "),
                t.name && (A += t.name),
                t.internalSubset && (A += t.internalSubset),
                t.publicId && (A += '"' + t.publicId + '"'),
                t.systemId && (A += '"' + t.systemId + '"'),
                (A += ">")),
            A
        );
    },
    bc = function (t, A, e) {
        t &&
            t.defaultView &&
            (A !== t.defaultView.pageXOffset || e !== t.defaultView.pageYOffset) &&
            t.defaultView.scrollTo(A, e);
    },
    xc = function (t) {
        var A = t[0],
            e = t[1],
            r = t[2];
        (A.scrollLeft = e), (A.scrollTop = r);
    },
    Dc = ":before",
    Sc = ":after",
    or = "___html2canvas___pseudoelement_before",
    cr = "___html2canvas___pseudoelement_after",
    pn = `{
    content: "" !important;
    display: none !important;
}`,
    Tc = function (t) {
        Oc(
            t,
            "." +
                or +
                Dc +
                pn +
                `
         .` +
                cr +
                Sc +
                pn
        );
    },
    Oc = function (t, A) {
        var e = t.ownerDocument;
        if (e) {
            var r = e.createElement("style");
            (r.textContent = A), t.appendChild(r);
        }
    },
    ys = (function () {
        function t() {}
        return (
            (t.getOrigin = function (A) {
                var e = t._link;
                return e ? ((e.href = A), (e.href = e.href), e.protocol + e.hostname + e.port) : "about:blank";
            }),
            (t.isSameOrigin = function (A) {
                return t.getOrigin(A) === t._origin;
            }),
            (t.setContext = function (A) {
                (t._link = A.document.createElement("a")), (t._origin = t.getOrigin(A.location.href));
            }),
            (t._origin = "about:blank"),
            t
        );
    })(),
    Mc = (function () {
        function t(A, e) {
            (this.context = A), (this._options = e), (this._cache = {});
        }
        return (
            (t.prototype.addImage = function (A) {
                var e = Promise.resolve();
                return (
                    this.has(A) || ((Vt(A) || Vc(A)) && (this._cache[A] = this.loadImage(A)).catch(function () {})), e
                );
            }),
            (t.prototype.match = function (A) {
                return this._cache[A];
            }),
            (t.prototype.loadImage = function (A) {
                return J(this, void 0, void 0, function () {
                    var e,
                        r,
                        n,
                        s,
                        B = this;
                    return _(this, function (i) {
                        switch (i.label) {
                            case 0:
                                return (
                                    (e = ys.isSameOrigin(A)),
                                    (r = !Gt(A) && this._options.useCORS === !0 && k.SUPPORT_CORS_IMAGES && !e),
                                    (n =
                                        !Gt(A) &&
                                        !e &&
                                        !Vt(A) &&
                                        typeof this._options.proxy == "string" &&
                                        k.SUPPORT_CORS_XHR &&
                                        !r),
                                    !e && this._options.allowTaint === !1 && !Gt(A) && !Vt(A) && !n && !r
                                        ? [2]
                                        : ((s = A), n ? [4, this.proxy(s)] : [3, 2])
                                );
                            case 1:
                                (s = i.sent()), (i.label = 2);
                            case 2:
                                return (
                                    this.context.logger.debug("Added image " + A.substring(0, 256)),
                                    [
                                        4,
                                        new Promise(function (a, o) {
                                            var c = new Image();
                                            (c.onload = function () {
                                                return a(c);
                                            }),
                                                (c.onerror = o),
                                                (kc(s) || r) && (c.crossOrigin = "anonymous"),
                                                (c.src = s),
                                                c.complete === !0 &&
                                                    setTimeout(function () {
                                                        return a(c);
                                                    }, 500),
                                                B._options.imageTimeout > 0 &&
                                                    setTimeout(function () {
                                                        return o(
                                                            "Timed out (" +
                                                                B._options.imageTimeout +
                                                                "ms) loading image"
                                                        );
                                                    }, B._options.imageTimeout);
                                        }),
                                    ]
                                );
                            case 3:
                                return [2, i.sent()];
                        }
                    });
                });
            }),
            (t.prototype.has = function (A) {
                return typeof this._cache[A] != "undefined";
            }),
            (t.prototype.keys = function () {
                return Promise.resolve(Object.keys(this._cache));
            }),
            (t.prototype.proxy = function (A) {
                var e = this,
                    r = this._options.proxy;
                if (!r) throw new Error("No proxy defined");
                var n = A.substring(0, 256);
                return new Promise(function (s, B) {
                    var i = k.SUPPORT_RESPONSE_TYPE ? "blob" : "text",
                        a = new XMLHttpRequest();
                    (a.onload = function () {
                        if (a.status === 200)
                            if (i === "text") s(a.response);
                            else {
                                var l = new FileReader();
                                l.addEventListener(
                                    "load",
                                    function () {
                                        return s(l.result);
                                    },
                                    !1
                                ),
                                    l.addEventListener(
                                        "error",
                                        function (g) {
                                            return B(g);
                                        },
                                        !1
                                    ),
                                    l.readAsDataURL(a.response);
                            }
                        else B("Failed to proxy resource " + n + " with status code " + a.status);
                    }),
                        (a.onerror = B);
                    var o = r.indexOf("?") > -1 ? "&" : "?";
                    if (
                        (a.open("GET", "" + r + o + "url=" + encodeURIComponent(A) + "&responseType=" + i),
                        i !== "text" && a instanceof XMLHttpRequest && (a.responseType = i),
                        e._options.imageTimeout)
                    ) {
                        var c = e._options.imageTimeout;
                        (a.timeout = c),
                            (a.ontimeout = function () {
                                return B("Timed out (" + c + "ms) proxying " + n);
                            });
                    }
                    a.send();
                });
            }),
            t
        );
    })(),
    Rc = /^data:image\/svg\+xml/i,
    Nc = /^data:image\/.*;base64,/i,
    Gc = /^data:image\/.*/i,
    Vc = function (t) {
        return k.SUPPORT_SVG_DRAWING || !Pc(t);
    },
    Gt = function (t) {
        return Gc.test(t);
    },
    kc = function (t) {
        return Nc.test(t);
    },
    Vt = function (t) {
        return t.substr(0, 4) === "blob";
    },
    Pc = function (t) {
        return t.substr(-3).toLowerCase() === "svg" || Rc.test(t);
    },
    C = (function () {
        function t(A, e) {
            (this.type = 0), (this.x = A), (this.y = e);
        }
        return (
            (t.prototype.add = function (A, e) {
                return new t(this.x + A, this.y + e);
            }),
            t
        );
    })(),
    XA = function (t, A, e) {
        return new C(t.x + (A.x - t.x) * e, t.y + (A.y - t.y) * e);
    },
    _e = (function () {
        function t(A, e, r, n) {
            (this.type = 1), (this.start = A), (this.startControl = e), (this.endControl = r), (this.end = n);
        }
        return (
            (t.prototype.subdivide = function (A, e) {
                var r = XA(this.start, this.startControl, A),
                    n = XA(this.startControl, this.endControl, A),
                    s = XA(this.endControl, this.end, A),
                    B = XA(r, n, A),
                    i = XA(n, s, A),
                    a = XA(B, i, A);
                return e ? new t(this.start, r, B, a) : new t(a, i, s, this.end);
            }),
            (t.prototype.add = function (A, e) {
                return new t(
                    this.start.add(A, e),
                    this.startControl.add(A, e),
                    this.endControl.add(A, e),
                    this.end.add(A, e)
                );
            }),
            (t.prototype.reverse = function () {
                return new t(this.end, this.endControl, this.startControl, this.start);
            }),
            t
        );
    })(),
    eA = function (t) {
        return t.type === 1;
    },
    _c = (function () {
        function t(A) {
            var e = A.styles,
                r = A.bounds,
                n = oe(e.borderTopLeftRadius, r.width, r.height),
                s = n[0],
                B = n[1],
                i = oe(e.borderTopRightRadius, r.width, r.height),
                a = i[0],
                o = i[1],
                c = oe(e.borderBottomRightRadius, r.width, r.height),
                l = c[0],
                g = c[1],
                w = oe(e.borderBottomLeftRadius, r.width, r.height),
                Q = w[0],
                f = w[1],
                H = [];
            H.push((s + a) / r.width),
                H.push((Q + l) / r.width),
                H.push((B + f) / r.height),
                H.push((o + g) / r.height);
            var d = Math.max.apply(Math, H);
            d > 1 && ((s /= d), (B /= d), (a /= d), (o /= d), (l /= d), (g /= d), (Q /= d), (f /= d));
            var F = r.width - a,
                L = r.height - g,
                v = r.width - l,
                p = r.height - f,
                h = e.borderTopWidth,
                m = e.borderRightWidth,
                y = e.borderBottomWidth,
                E = e.borderLeftWidth,
                M = D(e.paddingTop, A.bounds.width),
                Y = D(e.paddingRight, A.bounds.width),
                j = D(e.paddingBottom, A.bounds.width),
                b = D(e.paddingLeft, A.bounds.width);
            (this.topLeftBorderDoubleOuterBox =
                s > 0 || B > 0
                    ? S(r.left + E / 3, r.top + h / 3, s - E / 3, B - h / 3, K.TOP_LEFT)
                    : new C(r.left + E / 3, r.top + h / 3)),
                (this.topRightBorderDoubleOuterBox =
                    s > 0 || B > 0
                        ? S(r.left + F, r.top + h / 3, a - m / 3, o - h / 3, K.TOP_RIGHT)
                        : new C(r.left + r.width - m / 3, r.top + h / 3)),
                (this.bottomRightBorderDoubleOuterBox =
                    l > 0 || g > 0
                        ? S(r.left + v, r.top + L, l - m / 3, g - y / 3, K.BOTTOM_RIGHT)
                        : new C(r.left + r.width - m / 3, r.top + r.height - y / 3)),
                (this.bottomLeftBorderDoubleOuterBox =
                    Q > 0 || f > 0
                        ? S(r.left + E / 3, r.top + p, Q - E / 3, f - y / 3, K.BOTTOM_LEFT)
                        : new C(r.left + E / 3, r.top + r.height - y / 3)),
                (this.topLeftBorderDoubleInnerBox =
                    s > 0 || B > 0
                        ? S(r.left + (E * 2) / 3, r.top + (h * 2) / 3, s - (E * 2) / 3, B - (h * 2) / 3, K.TOP_LEFT)
                        : new C(r.left + (E * 2) / 3, r.top + (h * 2) / 3)),
                (this.topRightBorderDoubleInnerBox =
                    s > 0 || B > 0
                        ? S(r.left + F, r.top + (h * 2) / 3, a - (m * 2) / 3, o - (h * 2) / 3, K.TOP_RIGHT)
                        : new C(r.left + r.width - (m * 2) / 3, r.top + (h * 2) / 3)),
                (this.bottomRightBorderDoubleInnerBox =
                    l > 0 || g > 0
                        ? S(r.left + v, r.top + L, l - (m * 2) / 3, g - (y * 2) / 3, K.BOTTOM_RIGHT)
                        : new C(r.left + r.width - (m * 2) / 3, r.top + r.height - (y * 2) / 3)),
                (this.bottomLeftBorderDoubleInnerBox =
                    Q > 0 || f > 0
                        ? S(r.left + (E * 2) / 3, r.top + p, Q - (E * 2) / 3, f - (y * 2) / 3, K.BOTTOM_LEFT)
                        : new C(r.left + (E * 2) / 3, r.top + r.height - (y * 2) / 3)),
                (this.topLeftBorderStroke =
                    s > 0 || B > 0
                        ? S(r.left + E / 2, r.top + h / 2, s - E / 2, B - h / 2, K.TOP_LEFT)
                        : new C(r.left + E / 2, r.top + h / 2)),
                (this.topRightBorderStroke =
                    s > 0 || B > 0
                        ? S(r.left + F, r.top + h / 2, a - m / 2, o - h / 2, K.TOP_RIGHT)
                        : new C(r.left + r.width - m / 2, r.top + h / 2)),
                (this.bottomRightBorderStroke =
                    l > 0 || g > 0
                        ? S(r.left + v, r.top + L, l - m / 2, g - y / 2, K.BOTTOM_RIGHT)
                        : new C(r.left + r.width - m / 2, r.top + r.height - y / 2)),
                (this.bottomLeftBorderStroke =
                    Q > 0 || f > 0
                        ? S(r.left + E / 2, r.top + p, Q - E / 2, f - y / 2, K.BOTTOM_LEFT)
                        : new C(r.left + E / 2, r.top + r.height - y / 2)),
                (this.topLeftBorderBox = s > 0 || B > 0 ? S(r.left, r.top, s, B, K.TOP_LEFT) : new C(r.left, r.top)),
                (this.topRightBorderBox =
                    a > 0 || o > 0 ? S(r.left + F, r.top, a, o, K.TOP_RIGHT) : new C(r.left + r.width, r.top)),
                (this.bottomRightBorderBox =
                    l > 0 || g > 0
                        ? S(r.left + v, r.top + L, l, g, K.BOTTOM_RIGHT)
                        : new C(r.left + r.width, r.top + r.height)),
                (this.bottomLeftBorderBox =
                    Q > 0 || f > 0 ? S(r.left, r.top + p, Q, f, K.BOTTOM_LEFT) : new C(r.left, r.top + r.height)),
                (this.topLeftPaddingBox =
                    s > 0 || B > 0
                        ? S(r.left + E, r.top + h, Math.max(0, s - E), Math.max(0, B - h), K.TOP_LEFT)
                        : new C(r.left + E, r.top + h)),
                (this.topRightPaddingBox =
                    a > 0 || o > 0
                        ? S(
                              r.left + Math.min(F, r.width - m),
                              r.top + h,
                              F > r.width + m ? 0 : Math.max(0, a - m),
                              Math.max(0, o - h),
                              K.TOP_RIGHT
                          )
                        : new C(r.left + r.width - m, r.top + h)),
                (this.bottomRightPaddingBox =
                    l > 0 || g > 0
                        ? S(
                              r.left + Math.min(v, r.width - E),
                              r.top + Math.min(L, r.height - y),
                              Math.max(0, l - m),
                              Math.max(0, g - y),
                              K.BOTTOM_RIGHT
                          )
                        : new C(r.left + r.width - m, r.top + r.height - y)),
                (this.bottomLeftPaddingBox =
                    Q > 0 || f > 0
                        ? S(
                              r.left + E,
                              r.top + Math.min(p, r.height - y),
                              Math.max(0, Q - E),
                              Math.max(0, f - y),
                              K.BOTTOM_LEFT
                          )
                        : new C(r.left + E, r.top + r.height - y)),
                (this.topLeftContentBox =
                    s > 0 || B > 0
                        ? S(
                              r.left + E + b,
                              r.top + h + M,
                              Math.max(0, s - (E + b)),
                              Math.max(0, B - (h + M)),
                              K.TOP_LEFT
                          )
                        : new C(r.left + E + b, r.top + h + M)),
                (this.topRightContentBox =
                    a > 0 || o > 0
                        ? S(
                              r.left + Math.min(F, r.width + E + b),
                              r.top + h + M,
                              F > r.width + E + b ? 0 : a - E + b,
                              o - (h + M),
                              K.TOP_RIGHT
                          )
                        : new C(r.left + r.width - (m + Y), r.top + h + M)),
                (this.bottomRightContentBox =
                    l > 0 || g > 0
                        ? S(
                              r.left + Math.min(v, r.width - (E + b)),
                              r.top + Math.min(L, r.height + h + M),
                              Math.max(0, l - (m + Y)),
                              g - (y + j),
                              K.BOTTOM_RIGHT
                          )
                        : new C(r.left + r.width - (m + Y), r.top + r.height - (y + j))),
                (this.bottomLeftContentBox =
                    Q > 0 || f > 0
                        ? S(r.left + E + b, r.top + p, Math.max(0, Q - (E + b)), f - (y + j), K.BOTTOM_LEFT)
                        : new C(r.left + E + b, r.top + r.height - (y + j)));
        }
        return t;
    })(),
    K;
(function (t) {
    (t[(t.TOP_LEFT = 0)] = "TOP_LEFT"),
        (t[(t.TOP_RIGHT = 1)] = "TOP_RIGHT"),
        (t[(t.BOTTOM_RIGHT = 2)] = "BOTTOM_RIGHT"),
        (t[(t.BOTTOM_LEFT = 3)] = "BOTTOM_LEFT");
})(K || (K = {}));
var S = function (t, A, e, r, n) {
        var s = 4 * ((Math.sqrt(2) - 1) / 3),
            B = e * s,
            i = r * s,
            a = t + e,
            o = A + r;
        switch (n) {
            case K.TOP_LEFT:
                return new _e(new C(t, o), new C(t, o - i), new C(a - B, A), new C(a, A));
            case K.TOP_RIGHT:
                return new _e(new C(t, A), new C(t + B, A), new C(a, o - i), new C(a, o));
            case K.BOTTOM_RIGHT:
                return new _e(new C(a, A), new C(a, A + i), new C(t + B, o), new C(t, o));
            case K.BOTTOM_LEFT:
            default:
                return new _e(new C(a, o), new C(a - B, o), new C(t, A + i), new C(t, A));
        }
    },
    it = function (t) {
        return [t.topLeftBorderBox, t.topRightBorderBox, t.bottomRightBorderBox, t.bottomLeftBorderBox];
    },
    Xc = function (t) {
        return [t.topLeftContentBox, t.topRightContentBox, t.bottomRightContentBox, t.bottomLeftContentBox];
    },
    at = function (t) {
        return [t.topLeftPaddingBox, t.topRightPaddingBox, t.bottomRightPaddingBox, t.bottomLeftPaddingBox];
    },
    Jc = (function () {
        function t(A, e, r) {
            (this.offsetX = A), (this.offsetY = e), (this.matrix = r), (this.type = 0), (this.target = 6);
        }
        return t;
    })(),
    Xe = (function () {
        function t(A, e) {
            (this.path = A), (this.target = e), (this.type = 1);
        }
        return t;
    })(),
    Yc = (function () {
        function t(A) {
            (this.opacity = A), (this.type = 2), (this.target = 6);
        }
        return t;
    })(),
    Wc = function (t) {
        return t.type === 0;
    },
    Ls = function (t) {
        return t.type === 1;
    },
    Zc = function (t) {
        return t.type === 2;
    },
    En = function (t, A) {
        return t.length === A.length
            ? t.some(function (e, r) {
                  return e === A[r];
              })
            : !1;
    },
    qc = function (t, A, e, r, n) {
        return t.map(function (s, B) {
            switch (B) {
                case 0:
                    return s.add(A, e);
                case 1:
                    return s.add(A + r, e);
                case 2:
                    return s.add(A + r, e + n);
                case 3:
                    return s.add(A, e + n);
            }
            return s;
        });
    },
    Ks = (function () {
        function t(A) {
            (this.element = A),
                (this.inlineLevel = []),
                (this.nonInlineLevel = []),
                (this.negativeZIndex = []),
                (this.zeroOrAutoZIndexOrTransformedOrOpacity = []),
                (this.positiveZIndex = []),
                (this.nonPositionedFloats = []),
                (this.nonPositionedInlineLevel = []);
        }
        return t;
    })(),
    bs = (function () {
        function t(A, e) {
            if (
                ((this.container = A),
                (this.parent = e),
                (this.effects = []),
                (this.curves = new _c(this.container)),
                this.container.styles.opacity < 1 && this.effects.push(new Yc(this.container.styles.opacity)),
                this.container.styles.transform !== null)
            ) {
                var r = this.container.bounds.left + this.container.styles.transformOrigin[0].number,
                    n = this.container.bounds.top + this.container.styles.transformOrigin[1].number,
                    s = this.container.styles.transform;
                this.effects.push(new Jc(r, n, s));
            }
            if (this.container.styles.overflowX !== 0) {
                var B = it(this.curves),
                    i = at(this.curves);
                En(B, i)
                    ? this.effects.push(new Xe(B, 6))
                    : (this.effects.push(new Xe(B, 2)), this.effects.push(new Xe(i, 4)));
            }
        }
        return (
            (t.prototype.getEffects = function (A) {
                for (
                    var e = [2, 3].indexOf(this.container.styles.position) === -1,
                        r = this.parent,
                        n = this.effects.slice(0);
                    r;

                ) {
                    var s = r.effects.filter(function (a) {
                        return !Ls(a);
                    });
                    if (e || r.container.styles.position !== 0 || !r.parent) {
                        if (
                            (n.unshift.apply(n, s),
                            (e = [2, 3].indexOf(r.container.styles.position) === -1),
                            r.container.styles.overflowX !== 0)
                        ) {
                            var B = it(r.curves),
                                i = at(r.curves);
                            En(B, i) || n.unshift(new Xe(i, 6));
                        }
                    } else n.unshift.apply(n, s);
                    r = r.parent;
                }
                return n.filter(function (a) {
                    return N(a.target, A);
                });
            }),
            t
        );
    })(),
    lr = function (t, A, e, r) {
        t.container.elements.forEach(function (n) {
            var s = N(n.flags, 4),
                B = N(n.flags, 2),
                i = new bs(n, t);
            N(n.styles.display, 2048) && r.push(i);
            var a = N(n.flags, 8) ? [] : r;
            if (s || B) {
                var o = s || n.styles.isPositioned() ? e : A,
                    c = new Ks(i);
                if (n.styles.isPositioned() || n.styles.opacity < 1 || n.styles.isTransformed()) {
                    var l = n.styles.zIndex.order;
                    if (l < 0) {
                        var g = 0;
                        o.negativeZIndex.some(function (Q, f) {
                            return l > Q.element.container.styles.zIndex.order ? ((g = f), !1) : g > 0;
                        }),
                            o.negativeZIndex.splice(g, 0, c);
                    } else if (l > 0) {
                        var w = 0;
                        o.positiveZIndex.some(function (Q, f) {
                            return l >= Q.element.container.styles.zIndex.order ? ((w = f + 1), !1) : w > 0;
                        }),
                            o.positiveZIndex.splice(w, 0, c);
                    } else o.zeroOrAutoZIndexOrTransformedOrOpacity.push(c);
                } else n.styles.isFloating() ? o.nonPositionedFloats.push(c) : o.nonPositionedInlineLevel.push(c);
                lr(i, c, s ? c : e, a);
            } else n.styles.isInlineLevel() ? A.inlineLevel.push(i) : A.nonInlineLevel.push(i), lr(i, A, e, a);
            N(n.flags, 8) && xs(n, a);
        });
    },
    xs = function (t, A) {
        for (var e = t instanceof Br ? t.start : 1, r = t instanceof Br ? t.reversed : !1, n = 0; n < A.length; n++) {
            var s = A[n];
            s.container instanceof ws &&
                typeof s.container.value == "number" &&
                s.container.value !== 0 &&
                (e = s.container.value),
                (s.listValue = Ue(e, s.container.styles.listStyleType, !0)),
                (e += r ? -1 : 1);
        }
    },
    jc = function (t) {
        var A = new bs(t, null),
            e = new Ks(A),
            r = [];
        return lr(A, e, e, r), xs(A.container, r), e;
    },
    Hn = function (t, A) {
        switch (A) {
            case 0:
                return rA(t.topLeftBorderBox, t.topLeftPaddingBox, t.topRightBorderBox, t.topRightPaddingBox);
            case 1:
                return rA(t.topRightBorderBox, t.topRightPaddingBox, t.bottomRightBorderBox, t.bottomRightPaddingBox);
            case 2:
                return rA(
                    t.bottomRightBorderBox,
                    t.bottomRightPaddingBox,
                    t.bottomLeftBorderBox,
                    t.bottomLeftPaddingBox
                );
            case 3:
            default:
                return rA(t.bottomLeftBorderBox, t.bottomLeftPaddingBox, t.topLeftBorderBox, t.topLeftPaddingBox);
        }
    },
    zc = function (t, A) {
        switch (A) {
            case 0:
                return rA(
                    t.topLeftBorderBox,
                    t.topLeftBorderDoubleOuterBox,
                    t.topRightBorderBox,
                    t.topRightBorderDoubleOuterBox
                );
            case 1:
                return rA(
                    t.topRightBorderBox,
                    t.topRightBorderDoubleOuterBox,
                    t.bottomRightBorderBox,
                    t.bottomRightBorderDoubleOuterBox
                );
            case 2:
                return rA(
                    t.bottomRightBorderBox,
                    t.bottomRightBorderDoubleOuterBox,
                    t.bottomLeftBorderBox,
                    t.bottomLeftBorderDoubleOuterBox
                );
            case 3:
            default:
                return rA(
                    t.bottomLeftBorderBox,
                    t.bottomLeftBorderDoubleOuterBox,
                    t.topLeftBorderBox,
                    t.topLeftBorderDoubleOuterBox
                );
        }
    },
    $c = function (t, A) {
        switch (A) {
            case 0:
                return rA(
                    t.topLeftBorderDoubleInnerBox,
                    t.topLeftPaddingBox,
                    t.topRightBorderDoubleInnerBox,
                    t.topRightPaddingBox
                );
            case 1:
                return rA(
                    t.topRightBorderDoubleInnerBox,
                    t.topRightPaddingBox,
                    t.bottomRightBorderDoubleInnerBox,
                    t.bottomRightPaddingBox
                );
            case 2:
                return rA(
                    t.bottomRightBorderDoubleInnerBox,
                    t.bottomRightPaddingBox,
                    t.bottomLeftBorderDoubleInnerBox,
                    t.bottomLeftPaddingBox
                );
            case 3:
            default:
                return rA(
                    t.bottomLeftBorderDoubleInnerBox,
                    t.bottomLeftPaddingBox,
                    t.topLeftBorderDoubleInnerBox,
                    t.topLeftPaddingBox
                );
        }
    },
    Al = function (t, A) {
        switch (A) {
            case 0:
                return Je(t.topLeftBorderStroke, t.topRightBorderStroke);
            case 1:
                return Je(t.topRightBorderStroke, t.bottomRightBorderStroke);
            case 2:
                return Je(t.bottomRightBorderStroke, t.bottomLeftBorderStroke);
            case 3:
            default:
                return Je(t.bottomLeftBorderStroke, t.topLeftBorderStroke);
        }
    },
    Je = function (t, A) {
        var e = [];
        return eA(t) ? e.push(t.subdivide(0.5, !1)) : e.push(t), eA(A) ? e.push(A.subdivide(0.5, !0)) : e.push(A), e;
    },
    rA = function (t, A, e, r) {
        var n = [];
        return (
            eA(t) ? n.push(t.subdivide(0.5, !1)) : n.push(t),
            eA(e) ? n.push(e.subdivide(0.5, !0)) : n.push(e),
            eA(r) ? n.push(r.subdivide(0.5, !0).reverse()) : n.push(r),
            eA(A) ? n.push(A.subdivide(0.5, !1).reverse()) : n.push(A),
            n
        );
    },
    Ds = function (t) {
        var A = t.bounds,
            e = t.styles;
        return A.add(
            e.borderLeftWidth,
            e.borderTopWidth,
            -(e.borderRightWidth + e.borderLeftWidth),
            -(e.borderTopWidth + e.borderBottomWidth)
        );
    },
    ot = function (t) {
        var A = t.styles,
            e = t.bounds,
            r = D(A.paddingLeft, e.width),
            n = D(A.paddingRight, e.width),
            s = D(A.paddingTop, e.width),
            B = D(A.paddingBottom, e.width);
        return e.add(
            r + A.borderLeftWidth,
            s + A.borderTopWidth,
            -(A.borderRightWidth + A.borderLeftWidth + r + n),
            -(A.borderTopWidth + A.borderBottomWidth + s + B)
        );
    },
    el = function (t, A) {
        return t === 0 ? A.bounds : t === 2 ? ot(A) : Ds(A);
    },
    tl = function (t, A) {
        return t === 0 ? A.bounds : t === 2 ? ot(A) : Ds(A);
    },
    kt = function (t, A, e) {
        var r = el(WA(t.styles.backgroundOrigin, A), t),
            n = tl(WA(t.styles.backgroundClip, A), t),
            s = rl(WA(t.styles.backgroundSize, A), e, r),
            B = s[0],
            i = s[1],
            a = oe(WA(t.styles.backgroundPosition, A), r.width - B, r.height - i),
            o = nl(WA(t.styles.backgroundRepeat, A), a, s, r, n),
            c = Math.round(r.left + a[0]),
            l = Math.round(r.top + a[1]);
        return [o, c, l, B, i];
    },
    JA = function (t) {
        return x(t) && t.value === qA.AUTO;
    },
    Ye = function (t) {
        return typeof t == "number";
    },
    rl = function (t, A, e) {
        var r = A[0],
            n = A[1],
            s = A[2],
            B = t[0],
            i = t[1];
        if (!B) return [0, 0];
        if (R(B) && i && R(i)) return [D(B, e.width), D(i, e.height)];
        var a = Ye(s);
        if (x(B) && (B.value === qA.CONTAIN || B.value === qA.COVER)) {
            if (Ye(s)) {
                var o = e.width / e.height;
                return o < s != (B.value === qA.COVER) ? [e.width, e.width / s] : [e.height * s, e.height];
            }
            return [e.width, e.height];
        }
        var c = Ye(r),
            l = Ye(n),
            g = c || l;
        if (JA(B) && (!i || JA(i))) {
            if (c && l) return [r, n];
            if (!a && !g) return [e.width, e.height];
            if (g && a) {
                var w = c ? r : n * s,
                    Q = l ? n : r / s;
                return [w, Q];
            }
            var f = c ? r : e.width,
                H = l ? n : e.height;
            return [f, H];
        }
        if (a) {
            var d = 0,
                F = 0;
            return (
                R(B) ? (d = D(B, e.width)) : R(i) && (F = D(i, e.height)),
                JA(B) ? (d = F * s) : (!i || JA(i)) && (F = d / s),
                [d, F]
            );
        }
        var L = null,
            v = null;
        if (
            (R(B) ? (L = D(B, e.width)) : i && R(i) && (v = D(i, e.height)),
            L !== null && (!i || JA(i)) && (v = c && l ? (L / r) * n : e.height),
            v !== null && JA(B) && (L = c && l ? (v / n) * r : e.width),
            L !== null && v !== null)
        )
            return [L, v];
        throw new Error("Unable to calculate background-size for element");
    },
    WA = function (t, A) {
        var e = t[A];
        return typeof e == "undefined" ? t[0] : e;
    },
    nl = function (t, A, e, r, n) {
        var s = A[0],
            B = A[1],
            i = e[0],
            a = e[1];
        switch (t) {
            case 2:
                return [
                    new C(Math.round(r.left), Math.round(r.top + B)),
                    new C(Math.round(r.left + r.width), Math.round(r.top + B)),
                    new C(Math.round(r.left + r.width), Math.round(a + r.top + B)),
                    new C(Math.round(r.left), Math.round(a + r.top + B)),
                ];
            case 3:
                return [
                    new C(Math.round(r.left + s), Math.round(r.top)),
                    new C(Math.round(r.left + s + i), Math.round(r.top)),
                    new C(Math.round(r.left + s + i), Math.round(r.height + r.top)),
                    new C(Math.round(r.left + s), Math.round(r.height + r.top)),
                ];
            case 1:
                return [
                    new C(Math.round(r.left + s), Math.round(r.top + B)),
                    new C(Math.round(r.left + s + i), Math.round(r.top + B)),
                    new C(Math.round(r.left + s + i), Math.round(r.top + B + a)),
                    new C(Math.round(r.left + s), Math.round(r.top + B + a)),
                ];
            default:
                return [
                    new C(Math.round(n.left), Math.round(n.top)),
                    new C(Math.round(n.left + n.width), Math.round(n.top)),
                    new C(Math.round(n.left + n.width), Math.round(n.height + n.top)),
                    new C(Math.round(n.left), Math.round(n.height + n.top)),
                ];
        }
    },
    sl = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7",
    vn = "Hidden Text",
    Bl = (function () {
        function t(A) {
            (this._data = {}), (this._document = A);
        }
        return (
            (t.prototype.parseMetrics = function (A, e) {
                var r = this._document.createElement("div"),
                    n = this._document.createElement("img"),
                    s = this._document.createElement("span"),
                    B = this._document.body;
                (r.style.visibility = "hidden"),
                    (r.style.fontFamily = A),
                    (r.style.fontSize = e),
                    (r.style.margin = "0"),
                    (r.style.padding = "0"),
                    (r.style.whiteSpace = "nowrap"),
                    B.appendChild(r),
                    (n.src = sl),
                    (n.width = 1),
                    (n.height = 1),
                    (n.style.margin = "0"),
                    (n.style.padding = "0"),
                    (n.style.verticalAlign = "baseline"),
                    (s.style.fontFamily = A),
                    (s.style.fontSize = e),
                    (s.style.margin = "0"),
                    (s.style.padding = "0"),
                    s.appendChild(this._document.createTextNode(vn)),
                    r.appendChild(s),
                    r.appendChild(n);
                var i = n.offsetTop - s.offsetTop + 2;
                r.removeChild(s),
                    r.appendChild(this._document.createTextNode(vn)),
                    (r.style.lineHeight = "normal"),
                    (n.style.verticalAlign = "super");
                var a = n.offsetTop - r.offsetTop + 2;
                return B.removeChild(r), { baseline: i, middle: a };
            }),
            (t.prototype.getMetrics = function (A, e) {
                var r = A + " " + e;
                return typeof this._data[r] == "undefined" && (this._data[r] = this.parseMetrics(A, e)), this._data[r];
            }),
            t
        );
    })(),
    Ss = (function () {
        function t(A, e) {
            (this.context = A), (this.options = e);
        }
        return t;
    })(),
    il = 1e4,
    al = (function (t) {
        sA(A, t);
        function A(e, r) {
            var n = t.call(this, e, r) || this;
            return (
                (n._activeEffects = []),
                (n.canvas = r.canvas ? r.canvas : document.createElement("canvas")),
                (n.ctx = n.canvas.getContext("2d")),
                r.canvas ||
                    ((n.canvas.width = Math.floor(r.width * r.scale)),
                    (n.canvas.height = Math.floor(r.height * r.scale)),
                    (n.canvas.style.width = r.width + "px"),
                    (n.canvas.style.height = r.height + "px")),
                (n.fontMetrics = new Bl(document)),
                n.ctx.scale(n.options.scale, n.options.scale),
                n.ctx.translate(-r.x, -r.y),
                (n.ctx.textBaseline = "bottom"),
                (n._activeEffects = []),
                n.context.logger.debug(
                    "Canvas renderer initialized (" + r.width + "x" + r.height + ") with scale " + r.scale
                ),
                n
            );
        }
        return (
            (A.prototype.applyEffects = function (e) {
                for (var r = this; this._activeEffects.length; ) this.popEffect();
                e.forEach(function (n) {
                    return r.applyEffect(n);
                });
            }),
            (A.prototype.applyEffect = function (e) {
                this.ctx.save(),
                    Zc(e) && (this.ctx.globalAlpha = e.opacity),
                    Wc(e) &&
                        (this.ctx.translate(e.offsetX, e.offsetY),
                        this.ctx.transform(
                            e.matrix[0],
                            e.matrix[1],
                            e.matrix[2],
                            e.matrix[3],
                            e.matrix[4],
                            e.matrix[5]
                        ),
                        this.ctx.translate(-e.offsetX, -e.offsetY)),
                    Ls(e) && (this.path(e.path), this.ctx.clip()),
                    this._activeEffects.push(e);
            }),
            (A.prototype.popEffect = function () {
                this._activeEffects.pop(), this.ctx.restore();
            }),
            (A.prototype.renderStack = function (e) {
                return J(this, void 0, void 0, function () {
                    var r;
                    return _(this, function (n) {
                        switch (n.label) {
                            case 0:
                                return (
                                    (r = e.element.container.styles),
                                    r.isVisible() ? [4, this.renderStackContent(e)] : [3, 2]
                                );
                            case 1:
                                n.sent(), (n.label = 2);
                            case 2:
                                return [2];
                        }
                    });
                });
            }),
            (A.prototype.renderNode = function (e) {
                return J(this, void 0, void 0, function () {
                    return _(this, function (r) {
                        switch (r.label) {
                            case 0:
                                if (N(e.container.flags, 16)) debugger;
                                return e.container.styles.isVisible()
                                    ? [4, this.renderNodeBackgroundAndBorders(e)]
                                    : [3, 3];
                            case 1:
                                return r.sent(), [4, this.renderNodeContent(e)];
                            case 2:
                                r.sent(), (r.label = 3);
                            case 3:
                                return [2];
                        }
                    });
                });
            }),
            (A.prototype.renderTextWithLetterSpacing = function (e, r, n) {
                var s = this;
                if (r === 0) this.ctx.fillText(e.text, e.bounds.left, e.bounds.top + n);
                else {
                    var B = hr(e.text);
                    B.reduce(function (i, a) {
                        return s.ctx.fillText(a, i, e.bounds.top + n), i + s.ctx.measureText(a).width;
                    }, e.bounds.left);
                }
            }),
            (A.prototype.createFontStyle = function (e) {
                var r = e.fontVariant
                        .filter(function (B) {
                            return B === "normal" || B === "small-caps";
                        })
                        .join(""),
                    n = ul(e.fontFamily).join(", "),
                    s = de(e.fontSize) ? "" + e.fontSize.number + e.fontSize.unit : e.fontSize.number + "px";
                return [[e.fontStyle, r, e.fontWeight, s, n].join(" "), n, s];
            }),
            (A.prototype.renderTextNode = function (e, r) {
                return J(this, void 0, void 0, function () {
                    var n,
                        s,
                        B,
                        i,
                        a,
                        o,
                        c,
                        l,
                        g = this;
                    return _(this, function (w) {
                        return (
                            (n = this.createFontStyle(r)),
                            (s = n[0]),
                            (B = n[1]),
                            (i = n[2]),
                            (this.ctx.font = s),
                            (this.ctx.direction = r.direction === 1 ? "rtl" : "ltr"),
                            (this.ctx.textAlign = "left"),
                            (this.ctx.textBaseline = "alphabetic"),
                            (a = this.fontMetrics.getMetrics(B, i)),
                            (o = a.baseline),
                            (c = a.middle),
                            (l = r.paintOrder),
                            e.textBounds.forEach(function (Q) {
                                l.forEach(function (f) {
                                    switch (f) {
                                        case 0:
                                            (g.ctx.fillStyle = G(r.color)),
                                                g.renderTextWithLetterSpacing(Q, r.letterSpacing, o);
                                            var H = r.textShadow;
                                            H.length &&
                                                Q.text.trim().length &&
                                                (H.slice(0)
                                                    .reverse()
                                                    .forEach(function (d) {
                                                        (g.ctx.shadowColor = G(d.color)),
                                                            (g.ctx.shadowOffsetX = d.offsetX.number * g.options.scale),
                                                            (g.ctx.shadowOffsetY = d.offsetY.number * g.options.scale),
                                                            (g.ctx.shadowBlur = d.blur.number),
                                                            g.renderTextWithLetterSpacing(Q, r.letterSpacing, o);
                                                    }),
                                                (g.ctx.shadowColor = ""),
                                                (g.ctx.shadowOffsetX = 0),
                                                (g.ctx.shadowOffsetY = 0),
                                                (g.ctx.shadowBlur = 0)),
                                                r.textDecorationLine.length &&
                                                    ((g.ctx.fillStyle = G(r.textDecorationColor || r.color)),
                                                    r.textDecorationLine.forEach(function (d) {
                                                        switch (d) {
                                                            case 1:
                                                                g.ctx.fillRect(
                                                                    Q.bounds.left,
                                                                    Math.round(Q.bounds.top + o),
                                                                    Q.bounds.width,
                                                                    1
                                                                );
                                                                break;
                                                            case 2:
                                                                g.ctx.fillRect(
                                                                    Q.bounds.left,
                                                                    Math.round(Q.bounds.top),
                                                                    Q.bounds.width,
                                                                    1
                                                                );
                                                                break;
                                                            case 3:
                                                                g.ctx.fillRect(
                                                                    Q.bounds.left,
                                                                    Math.ceil(Q.bounds.top + c),
                                                                    Q.bounds.width,
                                                                    1
                                                                );
                                                                break;
                                                        }
                                                    }));
                                            break;
                                        case 1:
                                            r.webkitTextStrokeWidth &&
                                                Q.text.trim().length &&
                                                ((g.ctx.strokeStyle = G(r.webkitTextStrokeColor)),
                                                (g.ctx.lineWidth = r.webkitTextStrokeWidth),
                                                (g.ctx.lineJoin = window.chrome ? "miter" : "round"),
                                                g.ctx.strokeText(Q.text, Q.bounds.left, Q.bounds.top + o)),
                                                (g.ctx.strokeStyle = ""),
                                                (g.ctx.lineWidth = 0),
                                                (g.ctx.lineJoin = "miter");
                                            break;
                                    }
                                });
                            }),
                            [2]
                        );
                    });
                });
            }),
            (A.prototype.renderReplacedElement = function (e, r, n) {
                if (n && e.intrinsicWidth > 0 && e.intrinsicHeight > 0) {
                    var s = ot(e),
                        B = at(r);
                    this.path(B),
                        this.ctx.save(),
                        this.ctx.clip(),
                        this.ctx.drawImage(
                            n,
                            0,
                            0,
                            e.intrinsicWidth,
                            e.intrinsicHeight,
                            s.left,
                            s.top,
                            s.width,
                            s.height
                        ),
                        this.ctx.restore();
                }
            }),
            (A.prototype.renderNodeContent = function (e) {
                return J(this, void 0, void 0, function () {
                    var r, n, s, B, i, a, F, F, o, c, l, g, v, w, Q, p, f, H, d, F, L, v, p;
                    return _(this, function (h) {
                        switch (h.label) {
                            case 0:
                                this.applyEffects(e.getEffects(4)),
                                    (r = e.container),
                                    (n = e.curves),
                                    (s = r.styles),
                                    (B = 0),
                                    (i = r.textNodes),
                                    (h.label = 1);
                            case 1:
                                return B < i.length ? ((a = i[B]), [4, this.renderTextNode(a, s)]) : [3, 4];
                            case 2:
                                h.sent(), (h.label = 3);
                            case 3:
                                return B++, [3, 1];
                            case 4:
                                if (!(r instanceof gs)) return [3, 8];
                                h.label = 5;
                            case 5:
                                return h.trys.push([5, 7, , 8]), [4, this.context.cache.match(r.src)];
                            case 6:
                                return (F = h.sent()), this.renderReplacedElement(r, n, F), [3, 8];
                            case 7:
                                return h.sent(), this.context.logger.error("Error loading image " + r.src), [3, 8];
                            case 8:
                                if ((r instanceof us && this.renderReplacedElement(r, n, r.canvas), !(r instanceof Qs)))
                                    return [3, 12];
                                h.label = 9;
                            case 9:
                                return h.trys.push([9, 11, , 12]), [4, this.context.cache.match(r.svg)];
                            case 10:
                                return (F = h.sent()), this.renderReplacedElement(r, n, F), [3, 12];
                            case 11:
                                return (
                                    h.sent(),
                                    this.context.logger.error("Error loading svg " + r.svg.substring(0, 255)),
                                    [3, 12]
                                );
                            case 12:
                                return r instanceof hs && r.tree
                                    ? ((o = new A(this.context, {
                                          scale: this.options.scale,
                                          backgroundColor: r.backgroundColor,
                                          x: 0,
                                          y: 0,
                                          width: r.width,
                                          height: r.height,
                                      })),
                                      [4, o.render(r.tree)])
                                    : [3, 14];
                            case 13:
                                (c = h.sent()),
                                    r.width &&
                                        r.height &&
                                        this.ctx.drawImage(
                                            c,
                                            0,
                                            0,
                                            r.width,
                                            r.height,
                                            r.bounds.left,
                                            r.bounds.top,
                                            r.bounds.width,
                                            r.bounds.height
                                        ),
                                    (h.label = 14);
                            case 14:
                                if (
                                    (r instanceof Ur &&
                                        ((l = Math.min(r.bounds.width, r.bounds.height)),
                                        r.type === rt
                                            ? r.checked &&
                                              (this.ctx.save(),
                                              this.path([
                                                  new C(r.bounds.left + l * 0.39363, r.bounds.top + l * 0.79),
                                                  new C(r.bounds.left + l * 0.16, r.bounds.top + l * 0.5549),
                                                  new C(r.bounds.left + l * 0.27347, r.bounds.top + l * 0.44071),
                                                  new C(r.bounds.left + l * 0.39694, r.bounds.top + l * 0.5649),
                                                  new C(r.bounds.left + l * 0.72983, r.bounds.top + l * 0.23),
                                                  new C(r.bounds.left + l * 0.84, r.bounds.top + l * 0.34085),
                                                  new C(r.bounds.left + l * 0.39363, r.bounds.top + l * 0.79),
                                              ]),
                                              (this.ctx.fillStyle = G(gn)),
                                              this.ctx.fill(),
                                              this.ctx.restore())
                                            : r.type === nt &&
                                              r.checked &&
                                              (this.ctx.save(),
                                              this.ctx.beginPath(),
                                              this.ctx.arc(
                                                  r.bounds.left + l / 2,
                                                  r.bounds.top + l / 2,
                                                  l / 4,
                                                  0,
                                                  Math.PI * 2,
                                                  !0
                                              ),
                                              (this.ctx.fillStyle = G(gn)),
                                              this.ctx.fill(),
                                              this.ctx.restore())),
                                    ol(r) && r.value.length)
                                ) {
                                    switch (
                                        ((g = this.createFontStyle(s)),
                                        (v = g[0]),
                                        (w = g[1]),
                                        (Q = this.fontMetrics.getMetrics(v, w).baseline),
                                        (this.ctx.font = v),
                                        (this.ctx.fillStyle = G(s.color)),
                                        (this.ctx.textBaseline = "alphabetic"),
                                        (this.ctx.textAlign = ll(r.styles.textAlign)),
                                        (p = ot(r)),
                                        (f = 0),
                                        r.styles.textAlign)
                                    ) {
                                        case 1:
                                            f += p.width / 2;
                                            break;
                                        case 2:
                                            f += p.width;
                                            break;
                                    }
                                    (H = p.add(f, 0, 0, -p.height / 2 + 1)),
                                        this.ctx.save(),
                                        this.path([
                                            new C(p.left, p.top),
                                            new C(p.left + p.width, p.top),
                                            new C(p.left + p.width, p.top + p.height),
                                            new C(p.left, p.top + p.height),
                                        ]),
                                        this.ctx.clip(),
                                        this.renderTextWithLetterSpacing(new we(r.value, H), s.letterSpacing, Q),
                                        this.ctx.restore(),
                                        (this.ctx.textBaseline = "alphabetic"),
                                        (this.ctx.textAlign = "left");
                                }
                                if (!N(r.styles.display, 2048)) return [3, 20];
                                if (r.styles.listStyleImage === null) return [3, 19];
                                if (((d = r.styles.listStyleImage), d.type !== 0)) return [3, 18];
                                (F = void 0), (L = d.url), (h.label = 15);
                            case 15:
                                return h.trys.push([15, 17, , 18]), [4, this.context.cache.match(L)];
                            case 16:
                                return (
                                    (F = h.sent()),
                                    this.ctx.drawImage(F, r.bounds.left - (F.width + 10), r.bounds.top),
                                    [3, 18]
                                );
                            case 17:
                                return (
                                    h.sent(), this.context.logger.error("Error loading list-style-image " + L), [3, 18]
                                );
                            case 18:
                                return [3, 20];
                            case 19:
                                e.listValue &&
                                    r.styles.listStyleType !== -1 &&
                                    ((v = this.createFontStyle(s)[0]),
                                    (this.ctx.font = v),
                                    (this.ctx.fillStyle = G(s.color)),
                                    (this.ctx.textBaseline = "middle"),
                                    (this.ctx.textAlign = "right"),
                                    (p = new fA(
                                        r.bounds.left,
                                        r.bounds.top + D(r.styles.paddingTop, r.bounds.width),
                                        r.bounds.width,
                                        Wr(s.lineHeight, s.fontSize.number) / 2 + 1
                                    )),
                                    this.renderTextWithLetterSpacing(
                                        new we(e.listValue, p),
                                        s.letterSpacing,
                                        Wr(s.lineHeight, s.fontSize.number) / 2 + 2
                                    ),
                                    (this.ctx.textBaseline = "bottom"),
                                    (this.ctx.textAlign = "left")),
                                    (h.label = 20);
                            case 20:
                                return [2];
                        }
                    });
                });
            }),
            (A.prototype.renderStackContent = function (e) {
                return J(this, void 0, void 0, function () {
                    var r, n, d, s, B, d, i, a, d, o, c, d, l, g, d, w, Q, d, f, H, d;
                    return _(this, function (F) {
                        switch (F.label) {
                            case 0:
                                if (N(e.element.container.flags, 16)) debugger;
                                return [4, this.renderNodeBackgroundAndBorders(e.element)];
                            case 1:
                                F.sent(), (r = 0), (n = e.negativeZIndex), (F.label = 2);
                            case 2:
                                return r < n.length ? ((d = n[r]), [4, this.renderStack(d)]) : [3, 5];
                            case 3:
                                F.sent(), (F.label = 4);
                            case 4:
                                return r++, [3, 2];
                            case 5:
                                return [4, this.renderNodeContent(e.element)];
                            case 6:
                                F.sent(), (s = 0), (B = e.nonInlineLevel), (F.label = 7);
                            case 7:
                                return s < B.length ? ((d = B[s]), [4, this.renderNode(d)]) : [3, 10];
                            case 8:
                                F.sent(), (F.label = 9);
                            case 9:
                                return s++, [3, 7];
                            case 10:
                                (i = 0), (a = e.nonPositionedFloats), (F.label = 11);
                            case 11:
                                return i < a.length ? ((d = a[i]), [4, this.renderStack(d)]) : [3, 14];
                            case 12:
                                F.sent(), (F.label = 13);
                            case 13:
                                return i++, [3, 11];
                            case 14:
                                (o = 0), (c = e.nonPositionedInlineLevel), (F.label = 15);
                            case 15:
                                return o < c.length ? ((d = c[o]), [4, this.renderStack(d)]) : [3, 18];
                            case 16:
                                F.sent(), (F.label = 17);
                            case 17:
                                return o++, [3, 15];
                            case 18:
                                (l = 0), (g = e.inlineLevel), (F.label = 19);
                            case 19:
                                return l < g.length ? ((d = g[l]), [4, this.renderNode(d)]) : [3, 22];
                            case 20:
                                F.sent(), (F.label = 21);
                            case 21:
                                return l++, [3, 19];
                            case 22:
                                (w = 0), (Q = e.zeroOrAutoZIndexOrTransformedOrOpacity), (F.label = 23);
                            case 23:
                                return w < Q.length ? ((d = Q[w]), [4, this.renderStack(d)]) : [3, 26];
                            case 24:
                                F.sent(), (F.label = 25);
                            case 25:
                                return w++, [3, 23];
                            case 26:
                                (f = 0), (H = e.positiveZIndex), (F.label = 27);
                            case 27:
                                return f < H.length ? ((d = H[f]), [4, this.renderStack(d)]) : [3, 30];
                            case 28:
                                F.sent(), (F.label = 29);
                            case 29:
                                return f++, [3, 27];
                            case 30:
                                return [2];
                        }
                    });
                });
            }),
            (A.prototype.mask = function (e) {
                this.ctx.beginPath(),
                    this.ctx.moveTo(0, 0),
                    this.ctx.lineTo(this.canvas.width, 0),
                    this.ctx.lineTo(this.canvas.width, this.canvas.height),
                    this.ctx.lineTo(0, this.canvas.height),
                    this.ctx.lineTo(0, 0),
                    this.formatPath(e.slice(0).reverse()),
                    this.ctx.closePath();
            }),
            (A.prototype.path = function (e) {
                this.ctx.beginPath(), this.formatPath(e), this.ctx.closePath();
            }),
            (A.prototype.formatPath = function (e) {
                var r = this;
                e.forEach(function (n, s) {
                    var B = eA(n) ? n.start : n;
                    s === 0 ? r.ctx.moveTo(B.x, B.y) : r.ctx.lineTo(B.x, B.y),
                        eA(n) &&
                            r.ctx.bezierCurveTo(
                                n.startControl.x,
                                n.startControl.y,
                                n.endControl.x,
                                n.endControl.y,
                                n.end.x,
                                n.end.y
                            );
                });
            }),
            (A.prototype.renderRepeat = function (e, r, n, s) {
                this.path(e),
                    (this.ctx.fillStyle = r),
                    this.ctx.translate(n, s),
                    this.ctx.fill(),
                    this.ctx.translate(-n, -s);
            }),
            (A.prototype.resizeImage = function (e, r, n) {
                var s;
                if (e.width === r && e.height === n) return e;
                var B = (s = this.canvas.ownerDocument) !== null && s !== void 0 ? s : document,
                    i = B.createElement("canvas");
                (i.width = Math.max(1, r)), (i.height = Math.max(1, n));
                var a = i.getContext("2d");
                return a.drawImage(e, 0, 0, e.width, e.height, 0, 0, r, n), i;
            }),
            (A.prototype.renderBackgroundImage = function (e) {
                return J(this, void 0, void 0, function () {
                    var r, n, s, B, i, a;
                    return _(this, function (o) {
                        switch (o.label) {
                            case 0:
                                (r = e.styles.backgroundImage.length - 1),
                                    (n = function (c) {
                                        var l,
                                            g,
                                            w,
                                            M,
                                            W,
                                            Z,
                                            b,
                                            V,
                                            y,
                                            Q,
                                            M,
                                            W,
                                            Z,
                                            b,
                                            V,
                                            f,
                                            H,
                                            d,
                                            F,
                                            L,
                                            v,
                                            p,
                                            h,
                                            m,
                                            y,
                                            E,
                                            M,
                                            Y,
                                            j,
                                            b,
                                            V,
                                            CA,
                                            W,
                                            Z,
                                            LA,
                                            BA,
                                            hA,
                                            KA,
                                            bA,
                                            lA,
                                            xA,
                                            gA;
                                        return _(this, function (GA) {
                                            switch (GA.label) {
                                                case 0:
                                                    if (c.type !== 0) return [3, 5];
                                                    (l = void 0), (g = c.url), (GA.label = 1);
                                                case 1:
                                                    return GA.trys.push([1, 3, , 4]), [4, s.context.cache.match(g)];
                                                case 2:
                                                    return (l = GA.sent()), [3, 4];
                                                case 3:
                                                    return (
                                                        GA.sent(),
                                                        s.context.logger.error("Error loading background-image " + g),
                                                        [3, 4]
                                                    );
                                                case 4:
                                                    return (
                                                        l &&
                                                            ((w = kt(e, r, [l.width, l.height, l.width / l.height])),
                                                            (M = w[0]),
                                                            (W = w[1]),
                                                            (Z = w[2]),
                                                            (b = w[3]),
                                                            (V = w[4]),
                                                            (y = s.ctx.createPattern(s.resizeImage(l, b, V), "repeat")),
                                                            s.renderRepeat(M, y, W, Z)),
                                                        [3, 6]
                                                    );
                                                case 5:
                                                    Yi(c)
                                                        ? ((Q = kt(e, r, [null, null, null])),
                                                          (M = Q[0]),
                                                          (W = Q[1]),
                                                          (Z = Q[2]),
                                                          (b = Q[3]),
                                                          (V = Q[4]),
                                                          (f = ki(c.angle, b, V)),
                                                          (H = f[0]),
                                                          (d = f[1]),
                                                          (F = f[2]),
                                                          (L = f[3]),
                                                          (v = f[4]),
                                                          (p = document.createElement("canvas")),
                                                          (p.width = b),
                                                          (p.height = V),
                                                          (h = p.getContext("2d")),
                                                          (m = h.createLinearGradient(d, L, F, v)),
                                                          Jr(c.stops, H).forEach(function ($A) {
                                                              return m.addColorStop($A.stop, G($A.color));
                                                          }),
                                                          (h.fillStyle = m),
                                                          h.fillRect(0, 0, b, V),
                                                          b > 0 &&
                                                              V > 0 &&
                                                              ((y = s.ctx.createPattern(p, "repeat")),
                                                              s.renderRepeat(M, y, W, Z)))
                                                        : Wi(c) &&
                                                          ((E = kt(e, r, [null, null, null])),
                                                          (M = E[0]),
                                                          (Y = E[1]),
                                                          (j = E[2]),
                                                          (b = E[3]),
                                                          (V = E[4]),
                                                          (CA = c.position.length === 0 ? [wr] : c.position),
                                                          (W = D(CA[0], b)),
                                                          (Z = D(CA[CA.length - 1], V)),
                                                          (LA = Pi(c, W, Z, b, V)),
                                                          (BA = LA[0]),
                                                          (hA = LA[1]),
                                                          BA > 0 &&
                                                              hA > 0 &&
                                                              ((KA = s.ctx.createRadialGradient(
                                                                  Y + W,
                                                                  j + Z,
                                                                  0,
                                                                  Y + W,
                                                                  j + Z,
                                                                  BA
                                                              )),
                                                              Jr(c.stops, BA * 2).forEach(function ($A) {
                                                                  return KA.addColorStop($A.stop, G($A.color));
                                                              }),
                                                              s.path(M),
                                                              (s.ctx.fillStyle = KA),
                                                              BA !== hA
                                                                  ? ((bA = e.bounds.left + 0.5 * e.bounds.width),
                                                                    (lA = e.bounds.top + 0.5 * e.bounds.height),
                                                                    (xA = hA / BA),
                                                                    (gA = 1 / xA),
                                                                    s.ctx.save(),
                                                                    s.ctx.translate(bA, lA),
                                                                    s.ctx.transform(1, 0, 0, xA, 0, 0),
                                                                    s.ctx.translate(-bA, -lA),
                                                                    s.ctx.fillRect(Y, gA * (j - lA) + lA, b, V * gA),
                                                                    s.ctx.restore())
                                                                  : s.ctx.fill())),
                                                        (GA.label = 6);
                                                case 6:
                                                    return r--, [2];
                                            }
                                        });
                                    }),
                                    (s = this),
                                    (B = 0),
                                    (i = e.styles.backgroundImage.slice(0).reverse()),
                                    (o.label = 1);
                            case 1:
                                return B < i.length ? ((a = i[B]), [5, n(a)]) : [3, 4];
                            case 2:
                                o.sent(), (o.label = 3);
                            case 3:
                                return B++, [3, 1];
                            case 4:
                                return [2];
                        }
                    });
                });
            }),
            (A.prototype.renderSolidBorder = function (e, r, n) {
                return J(this, void 0, void 0, function () {
                    return _(this, function (s) {
                        return this.path(Hn(n, r)), (this.ctx.fillStyle = G(e)), this.ctx.fill(), [2];
                    });
                });
            }),
            (A.prototype.renderDoubleBorder = function (e, r, n, s) {
                return J(this, void 0, void 0, function () {
                    var B, i;
                    return _(this, function (a) {
                        switch (a.label) {
                            case 0:
                                return r < 3 ? [4, this.renderSolidBorder(e, n, s)] : [3, 2];
                            case 1:
                                return a.sent(), [2];
                            case 2:
                                return (
                                    (B = zc(s, n)),
                                    this.path(B),
                                    (this.ctx.fillStyle = G(e)),
                                    this.ctx.fill(),
                                    (i = $c(s, n)),
                                    this.path(i),
                                    this.ctx.fill(),
                                    [2]
                                );
                        }
                    });
                });
            }),
            (A.prototype.renderNodeBackgroundAndBorders = function (e) {
                return J(this, void 0, void 0, function () {
                    var r,
                        n,
                        s,
                        B,
                        i,
                        a,
                        o,
                        c,
                        l = this;
                    return _(this, function (g) {
                        switch (g.label) {
                            case 0:
                                return (
                                    this.applyEffects(e.getEffects(2)),
                                    (r = e.container.styles),
                                    (n = !mA(r.backgroundColor) || r.backgroundImage.length),
                                    (s = [
                                        { style: r.borderTopStyle, color: r.borderTopColor, width: r.borderTopWidth },
                                        {
                                            style: r.borderRightStyle,
                                            color: r.borderRightColor,
                                            width: r.borderRightWidth,
                                        },
                                        {
                                            style: r.borderBottomStyle,
                                            color: r.borderBottomColor,
                                            width: r.borderBottomWidth,
                                        },
                                        {
                                            style: r.borderLeftStyle,
                                            color: r.borderLeftColor,
                                            width: r.borderLeftWidth,
                                        },
                                    ]),
                                    (B = cl(WA(r.backgroundClip, 0), e.curves)),
                                    n || r.boxShadow.length
                                        ? (this.ctx.save(),
                                          this.path(B),
                                          this.ctx.clip(),
                                          mA(r.backgroundColor) ||
                                              ((this.ctx.fillStyle = G(r.backgroundColor)), this.ctx.fill()),
                                          [4, this.renderBackgroundImage(e.container)])
                                        : [3, 2]
                                );
                            case 1:
                                g.sent(),
                                    this.ctx.restore(),
                                    r.boxShadow
                                        .slice(0)
                                        .reverse()
                                        .forEach(function (w) {
                                            l.ctx.save();
                                            var Q = it(e.curves),
                                                f = w.inset ? 0 : il,
                                                H = qc(
                                                    Q,
                                                    -f + (w.inset ? 1 : -1) * w.spread.number,
                                                    (w.inset ? 1 : -1) * w.spread.number,
                                                    w.spread.number * (w.inset ? -2 : 2),
                                                    w.spread.number * (w.inset ? -2 : 2)
                                                );
                                            w.inset
                                                ? (l.path(Q), l.ctx.clip(), l.mask(H))
                                                : (l.mask(Q), l.ctx.clip(), l.path(H)),
                                                (l.ctx.shadowOffsetX = w.offsetX.number + f),
                                                (l.ctx.shadowOffsetY = w.offsetY.number),
                                                (l.ctx.shadowColor = G(w.color)),
                                                (l.ctx.shadowBlur = w.blur.number),
                                                (l.ctx.fillStyle = w.inset ? G(w.color) : "rgba(0,0,0,1)"),
                                                l.ctx.fill(),
                                                l.ctx.restore();
                                        }),
                                    (g.label = 2);
                            case 2:
                                (i = 0), (a = 0), (o = s), (g.label = 3);
                            case 3:
                                return a < o.length
                                    ? ((c = o[a]),
                                      c.style !== 0 && !mA(c.color) && c.width > 0
                                          ? c.style !== 2
                                              ? [3, 5]
                                              : [4, this.renderDashedDottedBorder(c.color, c.width, i, e.curves, 2)]
                                          : [3, 11])
                                    : [3, 13];
                            case 4:
                                return g.sent(), [3, 11];
                            case 5:
                                return c.style !== 3
                                    ? [3, 7]
                                    : [4, this.renderDashedDottedBorder(c.color, c.width, i, e.curves, 3)];
                            case 6:
                                return g.sent(), [3, 11];
                            case 7:
                                return c.style !== 4
                                    ? [3, 9]
                                    : [4, this.renderDoubleBorder(c.color, c.width, i, e.curves)];
                            case 8:
                                return g.sent(), [3, 11];
                            case 9:
                                return [4, this.renderSolidBorder(c.color, i, e.curves)];
                            case 10:
                                g.sent(), (g.label = 11);
                            case 11:
                                i++, (g.label = 12);
                            case 12:
                                return a++, [3, 3];
                            case 13:
                                return [2];
                        }
                    });
                });
            }),
            (A.prototype.renderDashedDottedBorder = function (e, r, n, s, B) {
                return J(this, void 0, void 0, function () {
                    var i, a, o, c, l, g, w, Q, f, H, d, F, L, v, p, h, p, h;
                    return _(this, function (m) {
                        return (
                            this.ctx.save(),
                            (i = Al(s, n)),
                            (a = Hn(s, n)),
                            B === 2 && (this.path(a), this.ctx.clip()),
                            eA(a[0]) ? ((o = a[0].start.x), (c = a[0].start.y)) : ((o = a[0].x), (c = a[0].y)),
                            eA(a[1]) ? ((l = a[1].end.x), (g = a[1].end.y)) : ((l = a[1].x), (g = a[1].y)),
                            n === 0 || n === 2 ? (w = Math.abs(o - l)) : (w = Math.abs(c - g)),
                            this.ctx.beginPath(),
                            B === 3 ? this.formatPath(i) : this.formatPath(a.slice(0, 2)),
                            (Q = r < 3 ? r * 3 : r * 2),
                            (f = r < 3 ? r * 2 : r),
                            B === 3 && ((Q = r), (f = r)),
                            (H = !0),
                            w <= Q * 2
                                ? (H = !1)
                                : w <= Q * 2 + f
                                ? ((d = w / (2 * Q + f)), (Q *= d), (f *= d))
                                : ((F = Math.floor((w + f) / (Q + f))),
                                  (L = (w - F * Q) / (F - 1)),
                                  (v = (w - (F + 1) * Q) / F),
                                  (f = v <= 0 || Math.abs(f - L) < Math.abs(f - v) ? L : v)),
                            H && (B === 3 ? this.ctx.setLineDash([0, Q + f]) : this.ctx.setLineDash([Q, f])),
                            B === 3
                                ? ((this.ctx.lineCap = "round"), (this.ctx.lineWidth = r))
                                : (this.ctx.lineWidth = r * 2 + 1.1),
                            (this.ctx.strokeStyle = G(e)),
                            this.ctx.stroke(),
                            this.ctx.setLineDash([]),
                            B === 2 &&
                                (eA(a[0]) &&
                                    ((p = a[3]),
                                    (h = a[0]),
                                    this.ctx.beginPath(),
                                    this.formatPath([new C(p.end.x, p.end.y), new C(h.start.x, h.start.y)]),
                                    this.ctx.stroke()),
                                eA(a[1]) &&
                                    ((p = a[1]),
                                    (h = a[2]),
                                    this.ctx.beginPath(),
                                    this.formatPath([new C(p.end.x, p.end.y), new C(h.start.x, h.start.y)]),
                                    this.ctx.stroke())),
                            this.ctx.restore(),
                            [2]
                        );
                    });
                });
            }),
            (A.prototype.render = function (e) {
                return J(this, void 0, void 0, function () {
                    var r;
                    return _(this, function (n) {
                        switch (n.label) {
                            case 0:
                                return (
                                    this.options.backgroundColor &&
                                        ((this.ctx.fillStyle = G(this.options.backgroundColor)),
                                        this.ctx.fillRect(
                                            this.options.x,
                                            this.options.y,
                                            this.options.width,
                                            this.options.height
                                        )),
                                    (r = jc(e)),
                                    [4, this.renderStack(r)]
                                );
                            case 1:
                                return n.sent(), this.applyEffects([]), [2, this.canvas];
                        }
                    });
                });
            }),
            A
        );
    })(Ss),
    ol = function (t) {
        return t instanceof Cs || t instanceof fs ? !0 : t instanceof Ur && t.type !== nt && t.type !== rt;
    },
    cl = function (t, A) {
        switch (t) {
            case 0:
                return it(A);
            case 2:
                return Xc(A);
            case 1:
            default:
                return at(A);
        }
    },
    ll = function (t) {
        switch (t) {
            case 1:
                return "center";
            case 2:
                return "right";
            case 0:
            default:
                return "left";
        }
    },
    gl = ["-apple-system", "system-ui"],
    ul = function (t) {
        return /iPhone OS 15_(0|1)/.test(window.navigator.userAgent)
            ? t.filter(function (A) {
                  return gl.indexOf(A) === -1;
              })
            : t;
    },
    Ql = (function (t) {
        sA(A, t);
        function A(e, r) {
            var n = t.call(this, e, r) || this;
            return (
                (n.canvas = r.canvas ? r.canvas : document.createElement("canvas")),
                (n.ctx = n.canvas.getContext("2d")),
                (n.options = r),
                (n.canvas.width = Math.floor(r.width * r.scale)),
                (n.canvas.height = Math.floor(r.height * r.scale)),
                (n.canvas.style.width = r.width + "px"),
                (n.canvas.style.height = r.height + "px"),
                n.ctx.scale(n.options.scale, n.options.scale),
                n.ctx.translate(-r.x, -r.y),
                n.context.logger.debug(
                    "EXPERIMENTAL ForeignObject renderer initialized (" +
                        r.width +
                        "x" +
                        r.height +
                        " at " +
                        r.x +
                        "," +
                        r.y +
                        ") with scale " +
                        r.scale
                ),
                n
            );
        }
        return (
            (A.prototype.render = function (e) {
                return J(this, void 0, void 0, function () {
                    var r, n;
                    return _(this, function (s) {
                        switch (s.label) {
                            case 0:
                                return (
                                    (r = sr(
                                        this.options.width * this.options.scale,
                                        this.options.height * this.options.scale,
                                        this.options.scale,
                                        this.options.scale,
                                        e
                                    )),
                                    [4, wl(r)]
                                );
                            case 1:
                                return (
                                    (n = s.sent()),
                                    this.options.backgroundColor &&
                                        ((this.ctx.fillStyle = G(this.options.backgroundColor)),
                                        this.ctx.fillRect(
                                            0,
                                            0,
                                            this.options.width * this.options.scale,
                                            this.options.height * this.options.scale
                                        )),
                                    this.ctx.drawImage(
                                        n,
                                        -this.options.x * this.options.scale,
                                        -this.options.y * this.options.scale
                                    ),
                                    [2, this.canvas]
                                );
                        }
                    });
                });
            }),
            A
        );
    })(Ss),
    wl = function (t) {
        return new Promise(function (A, e) {
            var r = new Image();
            (r.onload = function () {
                A(r);
            }),
                (r.onerror = e),
                (r.src =
                    "data:image/svg+xml;charset=utf-8," + encodeURIComponent(new XMLSerializer().serializeToString(t)));
        });
    },
    fl = (function () {
        function t(A) {
            var e = A.id,
                r = A.enabled;
            (this.id = e), (this.enabled = r), (this.start = Date.now());
        }
        return (
            (t.prototype.debug = function () {
                for (var A = [], e = 0; e < arguments.length; e++) A[e] = arguments[e];
                this.enabled &&
                    (typeof window != "undefined" && window.console && typeof console.debug == "function"
                        ? console.debug.apply(console, ve([this.id, this.getTime() + "ms"], A))
                        : this.info.apply(this, A));
            }),
            (t.prototype.getTime = function () {
                return Date.now() - this.start;
            }),
            (t.prototype.info = function () {
                for (var A = [], e = 0; e < arguments.length; e++) A[e] = arguments[e];
                this.enabled &&
                    typeof window != "undefined" &&
                    window.console &&
                    typeof console.info == "function" &&
                    console.info.apply(console, ve([this.id, this.getTime() + "ms"], A));
            }),
            (t.prototype.warn = function () {
                for (var A = [], e = 0; e < arguments.length; e++) A[e] = arguments[e];
                this.enabled &&
                    (typeof window != "undefined" && window.console && typeof console.warn == "function"
                        ? console.warn.apply(console, ve([this.id, this.getTime() + "ms"], A))
                        : this.info.apply(this, A));
            }),
            (t.prototype.error = function () {
                for (var A = [], e = 0; e < arguments.length; e++) A[e] = arguments[e];
                this.enabled &&
                    (typeof window != "undefined" && window.console && typeof console.error == "function"
                        ? console.error.apply(console, ve([this.id, this.getTime() + "ms"], A))
                        : this.info.apply(this, A));
            }),
            (t.instances = {}),
            t
        );
    })(),
    Cl = (function () {
        function t(A, e) {
            var r;
            (this.windowBounds = e),
                (this.instanceName = "#" + t.instanceCount++),
                (this.logger = new fl({ id: this.instanceName, enabled: A.logging })),
                (this.cache = (r = A.cache) !== null && r !== void 0 ? r : new Mc(this, A));
        }
        return (t.instanceCount = 1), t;
    })(),
    hl = function (t, A) {
        return A === void 0 && (A = {}), Ul(t, A);
    };
typeof window != "undefined" && ys.setContext(window);
var Ul = function (t, A) {
        return J(void 0, void 0, void 0, function () {
            var e,
                r,
                n,
                s,
                B,
                i,
                a,
                o,
                c,
                l,
                g,
                w,
                Q,
                f,
                H,
                d,
                F,
                L,
                v,
                p,
                m,
                h,
                m,
                y,
                E,
                M,
                Y,
                j,
                b,
                V,
                CA,
                W,
                Z,
                LA,
                BA,
                hA,
                KA,
                bA,
                lA,
                xA;
            return _(this, function (gA) {
                switch (gA.label) {
                    case 0:
                        if (!t || typeof t != "object")
                            return [2, Promise.reject("Invalid element provided as first argument")];
                        if (((e = t.ownerDocument), !e)) throw new Error("Element is not attached to a Document");
                        if (((r = e.defaultView), !r)) throw new Error("Document is not attached to a Window");
                        return (
                            (n = {
                                allowTaint: (y = A.allowTaint) !== null && y !== void 0 ? y : !1,
                                imageTimeout: (E = A.imageTimeout) !== null && E !== void 0 ? E : 15e3,
                                proxy: A.proxy,
                                useCORS: (M = A.useCORS) !== null && M !== void 0 ? M : !1,
                            }),
                            (s = _t({ logging: (Y = A.logging) !== null && Y !== void 0 ? Y : !0, cache: A.cache }, n)),
                            (B = {
                                windowWidth: (j = A.windowWidth) !== null && j !== void 0 ? j : r.innerWidth,
                                windowHeight: (b = A.windowHeight) !== null && b !== void 0 ? b : r.innerHeight,
                                scrollX: (V = A.scrollX) !== null && V !== void 0 ? V : r.pageXOffset,
                                scrollY: (CA = A.scrollY) !== null && CA !== void 0 ? CA : r.pageYOffset,
                            }),
                            (i = new fA(B.scrollX, B.scrollY, B.windowWidth, B.windowHeight)),
                            (a = new Cl(s, i)),
                            (o = (W = A.foreignObjectRendering) !== null && W !== void 0 ? W : !1),
                            (c = {
                                allowTaint: (Z = A.allowTaint) !== null && Z !== void 0 ? Z : !1,
                                onclone: A.onclone,
                                ignoreElements: A.ignoreElements,
                                inlineImages: o,
                                copyStyles: o,
                            }),
                            a.logger.debug(
                                "Starting document clone with size " +
                                    i.width +
                                    "x" +
                                    i.height +
                                    " scrolled to " +
                                    -i.left +
                                    "," +
                                    -i.top
                            ),
                            (l = new dn(a, t, c)),
                            (g = l.clonedReferenceElement),
                            g ? [4, l.toIFrame(e, i)] : [2, Promise.reject("Unable to find element in cloned iframe")]
                        );
                    case 1:
                        return (
                            (w = gA.sent()),
                            (Q = Fr(g) || Fc(g) ? Zs(g.ownerDocument) : lt(a, g)),
                            (f = Q.width),
                            (H = Q.height),
                            (d = Q.left),
                            (F = Q.top),
                            (L = Fl(a, g, A.backgroundColor)),
                            (v = {
                                canvas: A.canvas,
                                backgroundColor: L,
                                scale:
                                    (BA = (LA = A.scale) !== null && LA !== void 0 ? LA : r.devicePixelRatio) !==
                                        null && BA !== void 0
                                        ? BA
                                        : 1,
                                x: ((hA = A.x) !== null && hA !== void 0 ? hA : 0) + d,
                                y: ((KA = A.y) !== null && KA !== void 0 ? KA : 0) + F,
                                width: (bA = A.width) !== null && bA !== void 0 ? bA : Math.ceil(f),
                                height: (lA = A.height) !== null && lA !== void 0 ? lA : Math.ceil(H),
                            }),
                            o
                                ? (a.logger.debug("Document cloned, using foreign object rendering"),
                                  (m = new Ql(a, v)),
                                  [4, m.render(g)])
                                : [3, 3]
                        );
                    case 2:
                        return (p = gA.sent()), [3, 5];
                    case 3:
                        return (
                            a.logger.debug(
                                "Document cloned, element located at " +
                                    d +
                                    "," +
                                    F +
                                    " with size " +
                                    f +
                                    "x" +
                                    H +
                                    " using computed rendering"
                            ),
                            a.logger.debug("Starting DOM parsing"),
                            (h = Fs(a, g)),
                            L === h.styles.backgroundColor && (h.styles.backgroundColor = wA.TRANSPARENT),
                            a.logger.debug(
                                "Starting renderer for element at " +
                                    v.x +
                                    "," +
                                    v.y +
                                    " with size " +
                                    v.width +
                                    "x" +
                                    v.height
                            ),
                            (m = new al(a, v)),
                            [4, m.render(h)]
                        );
                    case 4:
                        (p = gA.sent()), (gA.label = 5);
                    case 5:
                        return (
                            (!((xA = A.removeContainer) !== null && xA !== void 0) || xA) &&
                                (dn.destroy(w) ||
                                    a.logger.error("Cannot detach cloned iframe as it is not in the DOM anymore")),
                            a.logger.debug("Finished rendering"),
                            [2, p]
                        );
                }
            });
        });
    },
    Fl = function (t, A, e) {
        var r = A.ownerDocument,
            n = r.documentElement ? ue(t, getComputedStyle(r.documentElement).backgroundColor) : wA.TRANSPARENT,
            s = r.body ? ue(t, getComputedStyle(r.body).backgroundColor) : wA.TRANSPARENT,
            B = typeof e == "string" ? ue(t, e) : e === null ? wA.TRANSPARENT : 4294967295;
        return A === r.documentElement ? (mA(n) ? (mA(s) ? B : s) : n) : B;
    };
const dl = ["name", "title", "id", "for", "href", "class"],
    u = { info: console.log, debug: console.debug, error: console.error },
    pl = () => new Date().getTime(),
    El = (t) => t.nodeType === Node.ELEMENT_NODE,
    We = (t) => ["text", "file", "select"].includes(t),
    In = (t) => {
        const A = t.tagName.toLowerCase();
        if ((u.debug("[elementClassifier] Classify tag:", A), A === "input")) {
            const e = t;
            switch ((u.debug("[elementClassifier] Element from input:", e), e.type)) {
                case "password":
                    return { type: "text", value: e.value };
                case "radio":
                    return { type: "radio", value: e.value };
                case "checkbox":
                    return { type: "checkbox", value: e.checked };
                case "file":
                    return { type: "file", value: e.value };
                case "email":
                case "tel":
                case "url":
                case "number":
                case "search":
                case "text":
                case "time":
                case "date":
                case "datetime-local":
                case "week":
                case "month":
                case "color":
                    return { type: "text", value: e.value };
                case "submit":
                case "image":
                case "range":
                case "reset":
                    return { type: e.type, value: void 0 };
            }
        } else if (A === "textarea") {
            const e = t;
            return u.debug("[elementClassifier] Element from textarea:", e), { type: "text", value: e.value };
        } else if (A === "select") {
            const e = t;
            return u.debug("[elementClassifier] Element from select:", e), { type: "select", value: e.value };
        } else if (A === "a") {
            const e = t;
            return u.debug("[classifyRawElement] Element from a:", e), { type: "a", value: e.href };
        } else if (A === "button") {
            const e = t;
            return u.debug("[elementClassifier] Element from button:", e), { type: "button", value: e.value };
        } else if (typeof t.onclick == "function" || typeof t.onmousedown == "function") {
            u.debug("[elementClassifier] Element from unknown element with onClick function:", t); //! TODO: This might need replacement with a better object
            return { type: "reset", value: void 0 };
        }
        u.debug("[elementClassifier] ERROR - Element could not be classified");
    },
    Hl = {
        parseNode(t, A, e, r) {
            if (
                (u.debug("Parsing Node:", t, "selectors:", A, "attributesArray:", e, "forceClassified:", r),
                t !== void 0)
            ) {
                u.debug("[scanner.parseNode] Creating hash...");
                let n = r || In(t);
                n === void 0 && t.parentElement && ((n = In(t.parentElement)), (t = t.parentElement)),
                    u.debug("[scanner.parseNode] Hash:", n);
                const s = vl.build(t, e, []);
                u.debug("[scanner.parseNode] Tree:", s);
                const B = pl();
                if (n !== void 0) {
                    const i = Il.build(s, t, n.type || "default");
                    u.debug("[scanner.parseNode] Built path:", i);
                    const a = Ae(DA({}, n), { selectors: A, time: B, path: i });
                    return u.debug("[scanner.parseNode] Parsed Node:", a), a;
                }
                u.error("[scanner.parseNode] Parsing failed. No Hash!");
                return;
            }
            u.error("[scanner.parseNode] Parsing failed. No Node!");
        },
    },
    $e = (t, A, e) => {
        try {
            u.debug("[classifyEvent] Classifying event:", t);
            const r = t.target;
            if (!(r instanceof HTMLElement || r instanceof SVGElement)) {
                u.debug("Element not HTMLElement:", r);
                return;
            }
            const n = A.buildStrategies(r).map((B) => A.getSelectorAsObject(B));
            if ((u.debug("[classifyEvent] Selectors (mapped) from builder:", n), n.length === 0)) {
                u.debug("[classifyEvent] Skipping committing due to no selectors");
                return;
            }
            const s = Hl.parseNode(r, n, dl, e);
            if ((u.debug("[classifyEvent] Element attributes:", s), !s)) {
                u.debug("[classifyEvent] Skipping committing due to no relevant attributes");
                return;
            }
            return s.type === "text" && s.value === ""
                ? (u.debug("[classifyEvent] Skipping saving empty text event"),
                  { selectors: [], node: void 0, skipError: !0 })
                : { selectors: n, node: s };
        } catch (r) {
            u.error("[classifyEvent] Could not classify event due to error:", r);
            return;
        }
    },
    vl = {
        _getIndex(t) {
            let A = !1,
                e = 0,
                r = 0;
            if (!t.parentNode) return 0;
            const n = t.parentNode.childNodes;
            for (let s = 0; s < n.length; s++) {
                n[s] === t && (A = !0);
                const B = n[s];
                El(B) && B.tagName === t.tagName && ((e += 1), (r = A ? r : r + 1));
            }
            return e > 1 ? r + 1 : 0;
        },
        _buildAttributes(t, A) {
            return A.map((r) => {
                let n;
                return (
                    r === "className"
                        ? (n = t.className.length > 0 ? t.className.split(" ") : null)
                        : r === "index"
                        ? (n = 1)
                        : (n = t.getAttribute(r)),
                    n ? { [`${r}`]: n } : null
                );
            }).filter((r) => r);
        },
        build(t, A, e) {
            if (
                (u.debug("[builder.build] Building for element:", t, "with attributes:", A, "and pathList:", e),
                !t || !t.parentNode || t.nodeType === Node.DOCUMENT_NODE)
            )
                return e;
            const r = this._buildAttributes(t, A);
            return e.push({ [`${t.tagName.toLowerCase()}`]: r }), this.build(t.parentNode, A, e);
        },
    },
    Il = {
        build(t, A, e) {
            const r = t[0],
                n = Object.keys(r)[0],
                s = r[n].reduce((o, c) => (o === "" ? this._getSubpath(o, c, n) : o), ""),
                B = `/${s}`;
            if (
                (u.debug("[locator.build] Building for Item:", r, "tag:", n, "p:", s, "path:", B),
                !A ||
                    this._found(["@id", "@for"], B) ||
                    (this._found(["@name"], B) && this._found(["select"], e)) ||
                    B === "/")
            )
                return B;
            const { count: i, index: a } = this._getIndex(B, A);
            return i > 1 && a > 1 ? `xpath=(${B})[${a}]` : B;
        },
        _found(t, A) {
            return t.some((e) => A.includes(e));
        },
        _getIndex(t, A) {
            let e = 1,
                r = 1,
                n;
            const s = document.evaluate(`.${t}`, document.body, null, XPathResult.ORDERED_NODE_ITERATOR_TYPE, null);
            for (; n === s.iterateNext(); ) n === A && (e = r), (r += 1);
            return { count: r, index: e };
        },
        _getSubpath(t, A, e) {
            return A.for != null
                ? `/${e}[@for="${A.for}"]`
                : A.class != null && typeof A.class != "number" && A.class.length > 0
                ? `/${e}[@class="${A.class}"]`
                : A.title != null
                ? `/${e}[@title="${A.title}"]`
                : A.href != null
                ? `/${e}[@href="${A.href}"]`
                : A.name != null
                ? `/${e}[@name="${A.name}"]`
                : A.id != null
                ? `/${e}[@id="${A.id}"]`
                : A.index != null
                ? `/${e}`
                : "";
        },
    },
    TA = {
        isElement: (t) => t.nodeType === window.Node.ELEMENT_NODE,
        isImage: (t) => t.nodeName.toUpperCase() === "IMG",
        isLink: (t) => t.nodeName.toUpperCase() === "A",
        isInput: (t) => t.nodeName.toUpperCase() === "INPUT",
        isLabel: (t) => t.nodeName.toUpperCase() === "LABEL",
    };
class ml {
    constructor(A) {
        (this.buildLocator = (e) =>
            UA(this, null, function* () {
                u.debug("[builder] Building locator for Element:", e), u.debug("[builder] Building source...");
                const r = `${this.window.location.protocol}//${this.window.location.host}/${this.window.location.pathname}${this.window.location.search}`;
                u.debug("[builder] Building tag...");
                const n = e.tagName;
                u.debug("[builder] Building alternatives...");
                const s = this.buildStrategies(e).map(([a, o]) => ({ strategy: a, value: o, matches: 1 }));
                u.debug("[builder] Building screenshot...");
                const i = (yield hl(e)).toDataURL("image/png");
                return (
                    u.debug("[builder] Returning locator..."),
                    { source: r, elementTag: n, alternatives: s, screenshot: i }
                );
            })),
            (this.buildStrategies = (e) => {
                u.debug("[builder] Building strategies for Element:", e);
                const r = [
                        ["id", this.buildId],
                        ["link", this.buildLinkText],
                        ["name", this.buildName],
                        ["css", this.buildCssFinder],
                        ["css:attributes", this.buildCssDataAttr],
                        ["xpath:link-text", this.buildXPathLink],
                        ["xpath:image", this.buildXPathImg],
                        ["xpath:attributes", this.buildXPathAttr],
                        ["xpath:relative-id", this.buildXPathIdRelative],
                        ["xpath:href", this.buildXPathHref],
                        ["xpath:position", this.buildXPathPosition],
                        ["xpath:inner-text", this.buildXPathInnerText],
                        ["xpath:input-label", this.buildXPathInputLabel],
                    ],
                    n = [];
                return (
                    r.forEach(([s, B]) => {
                        try {
                            const i = B(e);
                            i && (typeof i == "string" ? n.push([s, i]) : i.forEach((a) => n.push([s, a])));
                        } catch (i) {
                            u.error(`[builder] Failed to build '${s}': ${i}`);
                        }
                    }),
                    n
                );
            }),
            (this.logValidation = (e, r) => (
                e
                    ? u.debug("[builder] Selector validation PASSED for:", r)
                    : u.debug("[builder] Selector validation FAILED for:", r),
                e
            )),
            (this.validateId = (e) => document.getElementById(e) !== null),
            (this.validateName = (e) => document.getElementsByName(e) !== null),
            (this.validateXPath = (e) => document.evaluate(e, document, null, XPathResult.ANY_TYPE, null) !== null),
            (this.validateCSS = (e) => document.querySelector(e) !== null),
            (this.getSelectorAsObject = (e) => ({ strategy: e[0].split(":", 1)[0], value: e[1] })),
            (this.getElementByXPath = (e) =>
                document.evaluate(e, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue),
            (this.getXPathFromParent = (e) => {
                let r = "/" + e.nodeName.toLowerCase();
                const n = this.getNodeNumber(e);
                return n > 0 && (r += "[" + (n + 1) + "]"), r;
            }),
            (this.getNodeNumber = (e) => {
                var s;
                const r = ((s = e.parentNode) == null ? void 0 : s.childNodes) || [];
                let n = 0;
                for (let B = 0; B < r.length; B++) {
                    const i = r[B];
                    if (i.nodeName === e.nodeName) {
                        if (i === e) return n;
                        n++;
                    }
                }
                return 0;
            }),
            (this.getUniqueXPath = (e, r) => {
                if (r !== this.getElementByXPath(e)) {
                    const n = r.ownerDocument.evaluate(
                        e,
                        r.ownerDocument,
                        null,
                        XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
                        null
                    );
                    for (let s = 0, B = n.snapshotLength; s < B; s++) {
                        const i = "(" + e + ")[" + (s + 1) + "]";
                        if (r === this.getElementByXPath(i)) return i;
                    }
                }
                return e;
            }),
            (this.getXPathValue = (e) => {
                if (e.indexOf("'") < 0) return "'" + e + "'";
                if (e.indexOf('"') < 0) return '"' + e + '"';
                {
                    let r = "concat(",
                        n = "",
                        s = !1;
                    for (; !s; ) {
                        const B = e.indexOf("'"),
                            i = e.indexOf('"');
                        if (B < 0) {
                            (r += "'" + e + "'"), (s = !0);
                            break;
                        } else if (i < 0) {
                            (r += '"' + e + '"'), (s = !0);
                            break;
                        } else
                            i < B
                                ? ((n = e.substring(0, B)), (r += "'" + n + "'"), (e = e.substring(n.length)))
                                : ((n = e.substring(0, i)), (r += '"' + n + '"'), (e = e.substring(n.length)));
                        r += ",";
                    }
                    return (r += ")"), r;
                }
            }),
            (this.buildCssDataAttr = (e) => {
                const r = ["data-test", "data-test-id"];
                for (let n = 0; n < r.length; n++) {
                    const s = r[n],
                        B = e.getAttribute(s);
                    if (B) return "css=*[" + s + '="' + B + '"]';
                }
                return null;
            }),
            (this.buildId = (e) =>
                e.hasAttribute("id") && this.logValidation(this.validateId(e.id), "id:" + e.id) ? e.id : null),
            (this.buildLinkText = (e) => {
                if (!TA.isLink(e)) return null;
                const r = e.textContent || "";
                return r.match(/^\s*$/) ? null : r.replace(/\xA0/g, " ").replace(/^\s*(.*?)\s*$/, "$1");
            }),
            (this.buildName = (e) => {
                if (e.hasAttribute("name")) {
                    const r = e.getAttribute("name");
                    if (r && this.logValidation(this.validateName(r), "name:" + r)) return r;
                }
                return null;
            }),
            (this.buildCssFinder = (e) => {
                const r = Gs(e);
                return r && this.logValidation(this.validateCSS(r), "css:" + r) ? r : null;
            }),
            (this.buildXPathLink = (e) => {
                if (!TA.isLink(e)) return null;
                const r = e.textContent || "";
                if (r.match(/^\s*$/)) return null;
                const s = "//a[contains(text(),'" + r.replace(/^\s+/, "").replace(/\s+$/, "") + "')]",
                    B = this.getUniqueXPath(s, e);
                return B && this.logValidation(this.validateXPath(B), "xpath:" + B) ? B : null;
            }),
            (this.buildXPathImg = (e) => {
                if (!TA.isImage(e)) return null;
                let r = "";
                if (e.alt) r = "//img[@alt=" + this.getXPathValue(e.alt) + "]";
                else if (e.title) r = "//img[@title=" + this.getXPathValue(e.title) + "]";
                else if (e.src) r = "//img[contains(@src," + this.getXPathValue(e.src) + ")]";
                else return null;
                const n = this.getUniqueXPath(r, e);
                return n && this.logValidation(this.validateXPath(n), "xpath:" + n) ? n : null;
            }),
            (this.buildXPathAttr = (e) => {
                const r = ["id", "name", "value", "type", "action", "onclick"],
                    n = (a, o, c) => {
                        let l = "//" + a + "[";
                        for (let g = 0; g < o.length; g++) {
                            g > 0 && (l += " and ");
                            const w = o[g],
                                Q = this.getXPathValue(c[w]);
                            l += "@" + w + "=" + Q;
                        }
                        return (l += "]"), this.getUniqueXPath(l, e);
                    };
                if (!e.attributes) return null;
                const s = {},
                    B = e.attributes;
                for (let a = 0; a < B.length; a++) {
                    const o = B[a];
                    s[o.name] = o.value;
                }
                const i = [];
                for (let a = 0; a < r.length; a++) {
                    const o = r[a];
                    if (!s[o]) continue;
                    i.push(o);
                    const c = n(e.nodeName.toLowerCase(), i, s);
                    if (e === this.getElementByXPath(c) && c && this.logValidation(this.validateXPath(c), "xpath:" + c))
                        return c;
                }
                return null;
            }),
            (this.buildXPathIdRelative = (e) => {
                let r = "",
                    n = e;
                for (; n; ) {
                    const s = n.parentNode;
                    if (!s) return null;
                    if (((r = this.getXPathFromParent(n) + r), TA.isElement(s) && s.getAttribute("id"))) {
                        const B = s.nodeName.toLowerCase(),
                            i = this.getXPathValue(s.getAttribute("id") || ""),
                            a = "//" + B + "[@id=" + i + "]" + r,
                            o = this.getUniqueXPath(a, e);
                        if (o && this.logValidation(this.validateXPath(o), "xpath:" + o)) return o;
                    }
                    n = s;
                }
                return null;
            }),
            (this.buildXPathHref = (e) => {
                if (!e.hasAttribute("href")) return null;
                const r = e.getAttribute("href") || "";
                if (!r) return null;
                let n;
                r.search(/^http?:\/\//) >= 0
                    ? (n = "//a[@href=" + this.getXPathValue(r) + "]")
                    : (n = "//a[contains(@href, " + this.getXPathValue(r) + ")]");
                const s = this.getUniqueXPath(n, e);
                return s && this.logValidation(this.validateXPath(s), "xpath:" + s) ? s : null;
            }),
            (this.buildXPathPosition = (e) => {
                let r = "",
                    n = e;
                for (; n; ) {
                    const s = n.parentNode;
                    s ? (r = this.getXPathFromParent(n) + r) : (r = "/" + n.nodeName.toLowerCase() + r);
                    const B = "/" + r;
                    if (e === this.getElementByXPath(B) && B && this.logValidation(this.validateXPath(B), "xpath:" + B))
                        return B;
                    n = s;
                }
                return null;
            }),
            (this.buildXPathInnerText = (e) => {
                if (!(e instanceof HTMLElement) || !e.innerText) return null;
                const r = e.nodeName.toLowerCase(),
                    n = this.getXPathValue(e.innerText),
                    s = "//" + r + "[contains(.," + n + ")]",
                    B = this.getUniqueXPath(s, e);
                return B && this.logValidation(this.validateXPath(B), "xpath:" + B) ? s : null;
            }),
            (this.buildXPathInputLabel = (e) => {
                if (!TA.isInput(e)) return null;
                const r = document.getElementsByTagName("LABEL"),
                    n = {};
                for (let o = 0; o < r.length; o++) {
                    const c = r[o];
                    TA.isLabel(c) && c.htmlFor && document.getElementById(c.htmlFor) && (n[c.htmlFor] = c);
                }
                let s;
                if (e.id && Object.prototype.hasOwnProperty.call(e, "id")) s = n[e.id];
                else {
                    const o = e.parentNode;
                    if (!o) return null;
                    const c = [],
                        l = o.childNodes;
                    for (let g = 0; g < l.length; g++) {
                        const w = l[g];
                        TA.isLabel(w) && c.push(w);
                    }
                    if (c.length !== 1) return null;
                    s = c[0];
                }
                const i = "//label[contains(.," + this.getXPathValue(s.innerText) + ")]/../input",
                    a = this.getUniqueXPath(i, e);
                return a && this.logValidation(this.validateXPath(a), "xpath:" + a) ? a : null;
            }),
            (this.window = A);
    }
}
const gr = (t) =>
        new Promise((A) => {
            setTimeout(A, t);
        }),
    $ = {
        getFrameDiv() {
            const t = document.getElementById("inspector-frame") || document.createElement("div");
            return (t.id = "inspector-frame"), t;
        },
        focusElement(t) {
            u.debug("[frame] Focusing on element:", t),
                t.scrollIntoView({ behavior: "smooth", block: "center", inline: "nearest" });
            const A = document.createElement("div"),
                e = document.documentElement.getBoundingClientRect(),
                r = t.getBoundingClientRect();
            (A.id = "inspector-focus"),
                (A.style.left = `${r.left - e.left}px`),
                (A.style.top = `${r.top - e.top}px`),
                (A.style.width = `${r.width}px`),
                (A.style.height = `${r.height}px`),
                document.body.appendChild(A),
                setTimeout(() => {
                    document.body.removeChild(A);
                }, 500);
        },
        recorderSetErrorState() {
            u.debug("[frame.recorder] Settingstate to: error");
            const t = this.getFrameDiv();
            (t.className = "error"),
                setTimeout(() => {
                    u.debug("[frame.recorder] Resetting error state"), (t.className = "recorder");
                }, 1250);
        },
        pickerSetPauseState(t) {
            if ((u.debug("[frame.picker] Setting state to: paused"), t)) {
                const A = this.getFrameDiv();
                A.className = "paused";
            } else {
                const A = this.getFrameDiv();
                A.className = "picker";
            }
        },
        pickerSetSavingState(t) {
            if ((u.debug("[frame.picker] Setting state to: in_progress"), t)) {
                const A = this.getFrameDiv();
                A.className = "picker_in_progress";
            } else {
                const A = this.getFrameDiv();
                A.className = "picker";
            }
        },
    };
class yl {
    constructor(A, e, r) {
        (this.isPaused = !1),
            (this.setApp = (n) => {
                this.app = n;
            }),
            (this.setOnPick = (n) => {
                this.onPick = n;
            }),
            (this.setBuilder = (n) => {
                this.builder = n;
            }),
            (this.setNonStopRun = (n) => {
                this.nonStopRun = n;
            }),
            (this.addInfoBox = () => {
                const n = document.createElement("div");
                (n.id = "inspector-info-box"), (this.infoBox = n), document.body.appendChild(this.infoBox);
            }),
            (this._showPick = (n, s) => {
                const B = n.target;
                B !== s &&
                    (this._removeHighlights(),
                    B instanceof Element &&
                        (this.app === "recorder"
                            ? $e(n, this.builder, { type: "verify", value: void 0 }) && this._addHighlight(B)
                            : this._addHighlight(B),
                        (s = B)));
            }),
            (this._showDivInfo = (n) => {
                n.target instanceof HTMLElement &&
                    this.infoBox &&
                    this.builder &&
                    ((this.infoBox.textContent = "No element to target"),
                    (this.infoBox.style.left = `${n.pageX - 8}px`),
                    (this.infoBox.style.top = `${n.pageY - 20}px`));
            }),
            (this._addHighlight = (n) => {
                u.debug("[picker] Adding highlight to: ", n), n.setAttribute("data-inspector-highlight", "");
            }),
            (this._removeHighlights = () => {
                u.debug("[picker] Removing highlight...");
                const n = document.querySelectorAll("[data-inspector-highlight]");
                for (let s = 0; s < n.length; s++) n[s].removeAttribute("data-inspector-highlight");
            }),
            (this._pickElement = (n) =>
                UA(this, null, function* () {
                    var B;
                    u.debug("[picker] Picking Element:", n), n.preventDefault(), n.stopPropagation();
                    const s = n.target;
                    if (s instanceof HTMLElement || s instanceof SVGElement)
                        try {
                            this._removeHighlights(), $.pickerSetSavingState(!0);
                            const i = yield (B = this.builder) == null ? void 0 : B.buildLocator(s);
                            u.debug("[picker] Built locator:", i),
                                typeof this.onPick == "function"
                                    ? (u.debug("[picker] Calling callback:", this.onPick), this.onPick(i))
                                    : u.error("[picker] The onPick function is not set"),
                                setTimeout(() => {
                                    $.pickerSetSavingState();
                                }, 1500);
                        } catch (i) {
                            u.error(i);
                        } finally {
                            this.nonStopRun || this._removeAll();
                        }
                })),
            (this._checkCombination = (n) => {
                u.debug("[picker] Canceling Pick:", n);
                const s = n || window.event;
                !!s.shiftKey &&
                    ((s.key === "Escape" || s.keyCode === 27) && !this.isPaused
                        ? (u.debug("[picker] Pausing callbacks..."),
                          document.removeEventListener("mousemove", this._showPick, !0),
                          document.removeEventListener("click", this._pickElement, !0),
                          this._removeHighlights(),
                          u.debug("[picker] Pausing picker..."),
                          $.pickerSetPauseState(!0),
                          (this.isPaused = !0))
                        : (s.key === "Escape" || s.keyCode === 27) &&
                          (u.debug("[picker] Unpausing picker..."),
                          $.pickerSetPauseState(!1),
                          u.debug("[picker] Unpausing callbacks..."),
                          document.addEventListener("mousemove", this._showPick, !0),
                          document.addEventListener("click", this._pickElement, !0),
                          (this.isPaused = !1)));
            }),
            (this._removeAll = () => {
                u.debug("[picker] Removing all...");
                const n = document.getElementById("inspector-frame");
                n && document.body.removeChild(n);
                const s = document.getElementById("inspector-info-box");
                s && document.body.removeChild(s),
                    document.removeEventListener("mousemove", this._showPick, !0),
                    document.removeEventListener("click", this._pickElement, !0),
                    document.removeEventListener("keydown", this._checkCombination, !0),
                    this._removeHighlights();
            }),
            (this.builder = A),
            (this.app = e || "picker"),
            (this.nonStopRun = r);
    }
}
const mn = 750,
    Ll = () => {
        let t = !1;
        return {
            isLocked: t,
            acquire: () =>
                UA(exports, null, function* () {
                    u.debug("Acquiring lock...");
                    let r = !1;
                    for (
                        let n = 0;
                        n < 200 &&
                        (yield gr(10).then(() => {
                            t === !0 && (r = !0);
                        }),
                        !r);
                        n++
                    );
                    if (!r) throw Error("Timeout while acquiring lock");
                    t = !0;
                }),
            release: () =>
                UA(exports, null, function* () {
                    u.debug("Releasing lock..."), (t = !1);
                }),
        };
    };
class Kl {
    constructor(A, e) {
        (this.recordEvent = (n) => {
            this._removeListeners(), (this.actionsList = []);
            let s = document.getElementById("inspector-frame");
            !this.lock.isLocked &&
                !s &&
                ((s = document.createElement("div")),
                (s.id = "inspector-frame"),
                (s.className = "recorder"),
                document.body.appendChild(s)),
                (this.callback = n),
                this._addListeners();
        }),
            (this.stop = () => {
                this.callback && this.callback({ actionType: "stop", actions: void 0, url: document.URL }),
                    this.picker._removeAll(),
                    this._removeListeners();
            }),
            (this._addListeners = () => {
                document.addEventListener("mousemove", this.picker._showPick, !0),
                    document.addEventListener("click", this._handleClick, !0),
                    document.addEventListener("change", this._handleChange, !0),
                    document.addEventListener("keydown", this._handleKeyboardEvent, !0),
                    document.addEventListener("contextmenu", this._handleContextMenu, !0),
                    document.addEventListener("input", this._handleInputChange, !0);
            }),
            (this._removeListeners = () => {
                document.removeEventListener("mousemove", this.picker._showPick, !0),
                    document.removeEventListener("change", this._handleChange, !0),
                    document.removeEventListener("click", this._handleClick, !0),
                    document.removeEventListener("keydown", this._handleKeyboardEvent, !0),
                    document.removeEventListener("contextmenu", this._handleContextMenu, !0),
                    document.removeEventListener("input", this._handleInputChange, !0);
            }),
            (this._handleInputChange = (n) => {
                u.debug("[recorder] Input Change Event:", n), (this.inputEvent = n);
            }),
            (this._handleContextMenu = (n) => {
                const s = n.target;
                if (s instanceof HTMLElement || s instanceof SVGElement)
                    try {
                        n.preventDefault();
                        const B = $e(n, this.builder, { type: "verify", value: void 0 });
                        if (B === void 0 || B.node === void 0) {
                            (B != null && B.skipError) || $.recorderSetErrorState();
                            return;
                        }
                        const i = Ae(DA({}, B.node), { trigger: "click" });
                        u.debug("[recorder] Appending wait action:", i),
                            this.actionsList.push(i),
                            u.debug("[recorder] Event list:", this.actionsList),
                            $.focusElement(s),
                            u.debug("[recorder] Passing click event through callback -> WAITING..."),
                            this._sendEvents();
                    } catch (B) {
                        u.debug("[recorder] Skipping committing wait due to error", B), $.recorderSetErrorState();
                    }
            }),
            (this._handleChange = (n) => {
                u.debug("[recorder] Change Event:", n);
                const s = n.target;
                if (!(s instanceof HTMLElement || s instanceof SVGElement)) return;
                const B = $e(n, this.builder);
                if (B === void 0 || B.node === void 0) {
                    (B != null && B.skipError) || $.recorderSetErrorState();
                    return;
                }
                u.debug("[recorder] Is recording in progress:", this.lock.isLocked), this.lock.acquire();
                try {
                    if ((u.debug("[recorder] Is handled by change?:", We(B.node.type)), We(B.node.type))) {
                        const i = $.getFrameDiv();
                        (i.className = "recorder_in_progress"),
                            u.debug("[recorder] Preventing propagation..."),
                            n.preventDefault(),
                            n.stopPropagation();
                        const a = Ae(DA({}, B.node), { trigger: "change" });
                        u.debug("[recorder] Appending change action", a),
                            this.actionsList.push(a),
                            u.debug("[recorder] Event list:", this.actionsList),
                            u.debug("[recorder] Passing change event through callback"),
                            this._sendEvents(),
                            (() =>
                                UA(this, null, function* () {
                                    return yield gr(mn).then(() => {
                                        (i.className = "recorder"), this.lock.release();
                                    });
                                }))();
                    } else u.debug("[recorder] Skipping committing change - will be handled by onClick handler");
                } catch (i) {
                    u.debug("[recorder] Skipping committing change due to error", i), $.recorderSetErrorState();
                }
                (this.inputEvent = void 0), this.lock.release();
            }),
            (this._handleClick = (n) =>
                UA(this, null, function* () {
                    u.info("[recorder] Click Event:", n);
                    const s = n.target;
                    if (
                        (this.inputEvent && !this.lock.isLocked && this._handleChange(this.inputEvent),
                        !(s instanceof HTMLElement || s instanceof SVGElement))
                    )
                        return;
                    if (n.detail === -1) {
                        u.debug("[recorder] Dummy click. Exiting...");
                        return;
                    }
                    const B = $e(n, this.builder);
                    if (B === void 0 || B.node === void 0) {
                        (B != null && B.skipError) || $.recorderSetErrorState();
                        return;
                    }
                    u.debug("[recorder] Is recording in progress:", this.lock.isLocked), this.lock.acquire();
                    try {
                        if ((u.debug("[recorder] Is handled by change?:", We(B.node.type)), We(B.node.type)))
                            u.debug("[recorder] Skipping committing click - will be handled by onChange handler"),
                                this.lock.release();
                        else {
                            const i = document.getElementById("inspector-frame") || document.createElement("div");
                            (i.className = "recorder_in_progress"),
                                u.debug("[recorder] Preventing propagation..."),
                                n.preventDefault(),
                                n.stopPropagation();
                            const a = Ae(DA({}, B.node), { trigger: "click" });
                            u.debug("[recorder] Appending click action:", a),
                                this.actionsList.push(a),
                                u.debug("[recorder] Event list:", this.actionsList),
                                u.debug("[recorder] Passing click event through callback -> RECORDING..."),
                                this._sendEvents(),
                                (() =>
                                    UA(this, null, function* () {
                                        return yield gr(mn).then(() => {
                                            u.debug("[recorder] Pushing dummy event..."),
                                                (i.className = "recorder"),
                                                s.dispatchEvent(
                                                    new MouseEvent("click", {
                                                        bubbles: !0,
                                                        cancelable: !0,
                                                        view: window,
                                                        detail: -1,
                                                    })
                                                ),
                                                this.lock.release();
                                        });
                                    }))();
                        }
                    } catch (i) {
                        u.debug("[recorder] Skipping committing click due to error", i), $.recorderSetErrorState();
                    }
                })),
            (this._handleKeyboardEvent = (n) => {
                const s = n || window.event;
                (s.key === "Escape" || s.keyCode === 27) && this.stop(),
                    (s.key === "Tab" || s.keyCode === 9) && this.inputEvent && this._handleChange(this.inputEvent);
            }),
            (this._sendEvents = (n) => {
                this.callback
                    ? (this.callback({ actionType: "event", actions: this.actionsList, url: document.URL }),
                      u.debug("[recorder] Successfully invoked callback:", {
                          actionType: "event",
                          action: this.actionsList,
                          url: document.URL,
                      }),
                      n && (this.actionsList = []))
                    : u.debug("[recorder] No callback function defined");
            }),
            (this.builder = A),
            (this.picker = e),
            this.picker.setApp("recorder"),
            (this.actionsList = []),
            (this.lock = Ll()),
            (this.inputEvent = void 0);
        const r = document.getElementById("inspector-style") || document.createElement("style");
        (r.id = "inspector-style"), (r.type = "text/css"), document.head.appendChild(r);
    }
}
class bl {
    constructor() {
        (this.startPicker = (e, r) => {
            u.debug("[inspector] Starting picker..."),
                (this.onPickCallback = e),
                u.debug("[inspector] Will User Pick Non-Stop?", r),
                (this.nonStopRun = r),
                this.picker.setNonStopRun(r),
                this.picker.setOnPick(this.onPickCallback),
                this.picker._removeHighlights();
            const n = document.getElementById("inspector-frame") || document.createElement("div");
            (n.id = "inspector-frame"),
                (n.className = "picker"),
                document.body.appendChild(n),
                document.addEventListener("mousemove", this.picker._showPick, !0),
                document.addEventListener("click", this.picker._pickElement, !0),
                document.addEventListener("keydown", this.picker._checkCombination, !0);
        }),
            (this.highlightElements = (e) => {
                u.debug("[inspector] Highlighting elements:", e);
                for (let r = 0; r < e.length; r++) this.picker._addHighlight(e[r]);
            }),
            (this.describeElements = (e) => {
                u.debug("[inspector] Describing elements:", e);
                const r = [];
                for (let n = 0; n < e.length; n++) {
                    const s = e[n].cloneNode(!1).outerHTML;
                    r.push(s);
                }
                return r;
            }),
            (this.removeHighlights = () => {
                u.debug("[inspector] Removing highlights"), this.picker._removeHighlights();
            }),
            (this.cancelPick = () => {
                u.debug("[inspector] Cancelling pick and removing highlights"), this.picker._removeAll();
            }),
            (this.focusElement = (e) => $.focusElement(e)),
            (this.recordEvent = (e) => (u.debug("[inspector] Recording event..."), this.recorder.recordEvent(e))),
            (this.stopRecording = () => {
                u.debug("[inspector] Stopping recording..."), (window.InspectorStop = !0), this.recorder.stop();
            }),
            (this.builder = new ml(window)),
            (this.picker = new yl(this.builder)),
            (this.recorder = new Kl(this.builder, this.picker)),
            (this.nonStopRun = !1),
            (this.currentPick = void 0),
            (this.onPickCallback = void 0);
        const A = document.getElementById("inspector-style") || document.createElement("style");
        (A.id = "inspector-style"), (A.type = "text/css"), document.head.appendChild(A);
    }
}
window.Inspector = new bl();
