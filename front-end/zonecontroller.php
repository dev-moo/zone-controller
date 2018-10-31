<?php

include 'zone_config.php';
include 'udpcomms.php';


function get_value($val){

    switch ($val) {
        case "Off":
            return 0;
            break;
        case "Low":
            return 1;
            break;
        case "High":
            return 2;
            break;
    }
    
    return 0;
}

function set_value($val){

    switch ($val) {
        case 0:
            return "Off";
            break;
        case 1:
            return "Low";
            break;
        case 2:
            return "High";
            break;
    }
    
    return 0;
}

function change_zone($val){

    switch ($val) {
        case 'z1':
            return "Zone1";
            break;
        case 'z2':
            return "Zone2";
            break;
        case 'z3':
            return "Zone3";
            break;
        case 'z4':
            return "Zone4";
            break;       
        case 'z5':
            return "Zone5";
            break;
    }
    
    return 0;
}


function parse_status($status){
            
    $arr = array("z1" => get_value(json_decode($status)->Zone1));
    $arr += ["z2" => get_value(json_decode($status)->Zone2)];
    $arr += ["z3" => get_value(json_decode($status)->Zone3)];
    $arr += ["z4" => get_value(json_decode($status)->Zone4)];
    $arr += ["z5" => get_value(json_decode($status)->Zone5)];
    
    $arr = json_encode($arr);
    
    return $arr;
}


//Function to get status
function get_status(){
	
	Global $zcsocket;
	
	$zcsocket->transmit_data(json_encode(array("Operation" => "GET")));
    
	return $zcsocket->receive_data();
}


function operate($zone, $value){
    
    Global $zcsocket;
    
    $zone = change_zone($zone);
    $value = set_value($value);
    
    $zcsocket->transmit_data(json_encode(array("Operation" => "SET", "Zone" => $zone, "Value" => $value)));    
}


//Object to communicate over UDP
$zcsocket = new UDPComms($zc_server, $zc_port);


if(isset($_REQUEST)){
    
    $zone = $_REQUEST['Zone'];
    $value = $_REQUEST['Value'];
    
    operate($zone, $value);
    
}

echo parse_status(get_status());

?>