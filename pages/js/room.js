// Initializing variables
var canvas = document.getElementById("canvas");
var context = canvas.getContext("2d");

var b = new Board();
var map = reMapPiece();
refreshBoard(context, b, map);

// Todo: show english name on the board.
/*
var cn2en = new Array();
cn2en["车"] = "Chariot";
cn2en["马"] = "Horse";
cn2en["象"] = "Elephant";
cn2en["士"] = "Advisor";
cn2en["将"] = "King";
cn2en["炮"] = "Cannon";
cn2en["a"] = "Pawn";
*/
function refreshBoard(c, b, map) {
    c = canvas.getContext("2d");  // 需要重新布置画布才能及时显示棋子，画在canvas上的东西不会凭空产生消失
    c.clearRect(0, 0, canvas.width, canvas.height);
    drawBoard(c, b);
    drawPieces(c, b, map);
}



function Board() {
    this.cw = canvas.width / 9;
    this.ch = canvas.height / 10;
    this.w = canvas.width-this.cw;
    this.h = canvas.width-this.ch;
    this.pw =  this.cw / 2;
    this.ph =  this.ch / 2;
}

function drawLines(c, b, sx, sy, dx, dy) {
    c.moveTo(b.pw+sx, b.ph+sy);
    c.lineTo(b.pw+dx, b.ph+dy);
}

function drawBoard(c, b) {
    // draw grids, lines.
    c.beginPath();
    c.rect(0,0,canvas.width,canvas.height);
    c.lineWidth = 3;
    c.strokeStyle = "black";
    c.stroke();

    for(var i=0; i<=8; i++) {
        drawLines(c, b, b.cw*i, 0, b.cw*i, b.ch*9)
    }
    for(var i=0; i<=9; i++) {
        drawLines(c, b, 0, b.ch*i, b.cw*8, b.ch*i);
    }
    drawLines(c, b, b.cw*3, 0, b.cw*5, b.ch*2);
    drawLines(c, b, b.cw*5, 0, b.cw*3, b.ch*2);
    drawLines(c, b, b.cw*3, b.ch*7, b.cw*5, b.ch*9);
    drawLines(c, b, b.cw*3, b.ch*9, b.cw*5, b.ch*7);
    c.lineWidth = 3;
    c.strokeStyle = "black";
    c.stroke();
    c.closePath();

    // draw river
    c.beginPath();
    c.rect(b.pw+2, b.ch*5-b.ph+2, b.cw*8-4, b.ch-4);
    c.fillStyle='white';
    c.fill();
    c.closePath();

}

function Piece( piece_id, faction, piece_name) {
    this.f = faction;
    this.pid= piece_id;
    this.pn= piece_name;
}


function reMapPiece() {
    var b = [];
    var ppos = [];
    for(var i=0; i<=9; i++){
        b[i] = [];
        ppos[i] = [];

        for(var j=0; j<=8; j++){
            b[i][j] = new Piece("", "", "");
        }
    }
    ppos[0] = ["车", "马", "象", "士", "将", "士", "象", "马", "车"];
    ppos[1] = ["", "", "", "", "", "", "", "", ""];
    ppos[2] = ["",   "炮", "",   "",   "",  "",   "",   "炮", ""];
    ppos[3] = ["兵",  "",  "兵", "",  "兵", "",    "兵", "",  "兵"];
    ppos[4] = ppos[1];
    ppos[5] = ppos[1];
    ppos[6] = ppos[3];
    ppos[7] = ppos[2];
    ppos[8] = ppos[1];
    ppos[9] = ppos[0];



    for(var i=0; i<=9; i++){
        for(var j=0; j<=8; j++){
            b[i][j].f = i>5?'red':'black';
            b[i][j].pn = ppos[i][j];
            b[i][j].pid = i.toString() + j.toString();
        }
    }

    turn = 0;

    return b;
}

function drawPieces(c, b, m) {
    if(m !== null){
        for(var i=0; i<=9; i++){
            for(var j=0; j<=8; j++){
                if(m[i][j].pn) {
                    c.beginPath();

                    c.arc(b.cw*j+b.pw, b.ch*i+b.ph, b.pw-6, 0, Math.PI*2);
                    c.strokeStyle = m[i][j].f;
                    c.fillStyle = "white";
                    c.fill();
                    c.stroke();

                    c.font = "35px Arial bold";
                    c.fillStyle = m[i][j].f;
                    c.textBaseline="middle"
                    c.fillText(m[i][j].pn, b.cw*j+b.pw/2, b.ch*i+b.ph+3);

                    /*
                    c.font = "20px Arial bold";
                    c.fillStyle = m[i][j].f;
                    c.textBaseline="middle"
                    c.fillText(cn2en[m[i][j].pn], b.cw*j+b.pw/3, b.ch*i+b.ph+3);
                    */
                    c.closePath();
                }
            }
        }

    }

}
