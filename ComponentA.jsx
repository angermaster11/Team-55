import React,{useState,createContext} from 'react';
import ComponentB from "./ComponentB.jsx";

export const UserContext = createContext();
function ComponentA(){

    const [user, setUser] = useState("BroCode");
    return(
        <div className="box">
            <h1>Component A</h1>
            <p>Hello {user}</p>
            <UserContext value={user}>
                <ComponentB user={user}/>
            </UserContext>
        </div>
    )
}

export default ComponentA;