const mongoose=require("mongoose")
const axios=require("axios")


const fetchUserDetails=(async(req,res)=>{

    const token=req.cookies.github_access_token;
    console.log("TOKEN:", token);

    const response=await axios.get("https://api.github.com/user" , 
        {
            headers:{
                Authorization:`Bearer ${token}`
            }
        }
    );

    return res.json(response);
})

module.exports={
    fetchUserDetails
}