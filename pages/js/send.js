// sending changes to server
// sid, uid, cid are sent in cookies


var resetTimer = 0
// connect to boardcast service of the server
function wss(ip, port, page, para) {
    if("WebSocket" in window){
        var url = "wss://" + ip + ":" + port + "/" + page + "?" + para;
        // I can either send para here or in onopen function.

        var ws= new WebSocket(url);
        ws.onopen=function () {
            //ws.send(JSON.stringify("WebSocketOpen"));
            //ws.send(JSON.stringify(map))
        };
        ws.onmessage=function (msg) {
            var m = msg.data;
            console.log("Got an msg："+m);
            if(m.startsWith("Error:")) {
                alert(m);
                console.log("Got an Error："+m);
            }else if(m.startsWith("Hello:")){
                if (document.getElementById("w").innerText === "None"){
                    console.log("Got an Hello：" + m);
                    var p2txt = document.getElementById("p2");
                    var p1txt = document.getElementById("p1");
                    m = m.split(":")[1];
                    console.log(p2txt.innerText, "None", p1txt.innerText.slice(5,), m);
                    if ((p2txt.innerText === "None") && (p1txt.innerText.slice(5,) !== m)) {
                        p2txt.innerText = m;
                        document.getElementById("s").innerText = "gaming";
                    }
                    alert(m + "has connected.");
                    resetTimer = 1;
                }else{
                    console.log("Got an Hello from a closed room：" + m);
                }

            }else if(m.startsWith("Winner:")){
                console.log("Got an Winner："+m);
                alert(m);
                m = m.split(":")[1];
                document.getElementById("w").innerText = m;
                document.getElementById("s").innerText = "closed";
                inputtxt.disabled = "disabled";

            }else if(m.startsWith("Rec::")){
                console.log("Got records："+m);
                m = m.split("::")[1];
                m = m.split(";");
                m_l = m.length;
                document.getElementById("recs").innerHTML = "";
                for(var i = m_l-1; i>0; i--){
                    var tag_li=document.createElement("li");
                    tag_li.innerText = i.toString()+": "+m[i];
                    tag_li.style="color:"+m[i].split("[")[0];
                    document.getElementById("recs").appendChild(tag_li);
                }
            }else if(m.startsWith("SW:")){
                console.log("Got SW："+m);
                var ttxt = document.getElementById("t");
                ttxt.innerText= m.split(":")[1];

            }else if(m.startsWith("Timeout:")){
                console.log("Got Timeout："+m);
                resetTimer = 0;
                if (document.getElementById("s").innerText !== "closed"){
                    alert(m+" disconnected. 5 mins Return Timer started.");
                    countDown(60*5, ws); // 5min count down plus 3 second processing time
            }


            }else{
                // console.log("Got an map："+m);
                // newmap = ;
                refreshBoard(context, b, JSON.parse(m));
            }
        };
        ws.onclose=function () {
            if (document.getElementById("s").innerText !== "closed"){
                alert("Connection to server is lost, please refresh the page.");
                console.log("Connection closed");
            }

        };
        return ws;
    }else{
        alert("Your browser does not seem to support Websocket. Try another modern browser.");
    }
}

function countDown(count, wsobj) {
    document.getElementById("timer").innerText = count;

    if (count === -3) {
        wsobj.send("timeoutcheck");
    }else if (resetTimer === 1){
        document.getElementById("timer").innerText = 300;
    }else{
        count -= 1;
        setTimeout(function () {
            countDown(count, wsobj);
        }, 1000);
    }

}


/*
function post(rid, piece_id, start_pos, end_pos) {
    $.ajax({
        type: "post",
        url: "/data",
        data: {
            action: 1,
            rid: rid,
            dataType: "json",
            contentType: "application/json",
            xhrFields: {
                withCredentials: true
            },
            pid: piece_id,
            spos: start_pos,
            epos: end_pos
        },
        success: function(response) {
            if (response) {
                var resp = JSON.parse(response);

                // if the action is permitted.
                if(resp.is_valid === true) {
                    changeChess();
                }else{
                    alert("invalid operation:" + resp.v_msg);
                }

                // if the game is over.
                if(resp.is_over === true){
                        alert("winner is "+resp.winner);
                        init()
                }
            }
            else {
                alert("No response from the game server. Please try again.");
            }
        },
        error: function(response) {
            alert("Retrieving data failed: " + response.status);
        }
    });
}

// intervally query changes from server
function query(rid) {
    $.ajax({
        type: "post",
        url : "/data",
        dataType: "json",
        contentType: "application/json",
        xhrFields: {
            withCredentials: true
        },
        data: {
            action: 0,
            rid: rid
        },
        success: function(response) {
            if (response) {
                var resp = JSON.parse(response);
                // if the action is permitted.
                if (resp.has_changes === true) {
                    new_board = JSON.parse(resp.b);
                    drawBoard();
                    drawPieces(new_board)
                }
            }
        },
        error: function(response) {
            alert("Retrieving data failed: " + response.status);
        }
    });
}

*/

