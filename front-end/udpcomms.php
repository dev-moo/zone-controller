
<?php

class UDPComms{
	
	private $sock;
	public $server;
	public $port;
	
	
	private function create_socket(){
	 
		if(!($s = socket_create(AF_INET, SOCK_DGRAM, 0))){
		                           
			$errorcode = socket_last_error();
			$errormsg = socket_strerror($errorcode);
			 
			die("Couldn't create socket: [$errorcode] $errormsg \n");
			
			return false;
		}
        
        //Set timeout to 10 seconds
        socket_set_option($s, SOL_SOCKET, SO_RCVTIMEO, array('sec' => 10, 'usec' => 0));
    
		return $s;
	}
	
	public function __construct($s, $p) {
		$this->server = $s;
		$this->port = $p;
		$this->sock = $this->create_socket();
	}
	

	public function transmit_data($data){
		
		//Send the message to the server
		if( ! socket_sendto($this->sock, $data , strlen($data) , 0 , $this->server , $this->port))
		{
			$errorcode = socket_last_error();
			$errormsg = socket_strerror($errorcode);
			
			die("Could not send data: [$errorcode] $errormsg \n");
			
			return false;
		}

		return true;
	}
    
	public function receive_data(){
        
        if(socket_recv($this->sock , $reply , 2048, MSG_WAITALL)){
            return $reply;
        }
        
        //echo "Connection failed :(";

        return false;
		
	}	    
	
	public function receive_data_OLD(){
				
		$data_received = false;
        
        if(socket_recv($this->sock , $reply , 2048, MSG_WAITALL)){
            $data_received = true;
        }
		
		
		if(!$data_received){
			return false;
		}
			
		
		if($reply == "failed"){
			echo "Connection failed :(";
			return false;
		}			
		
		return $reply;
	}	
}



?>