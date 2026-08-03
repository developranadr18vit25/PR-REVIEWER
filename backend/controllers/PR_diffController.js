const axios=require('axios');
const mongoose=require("mongoose")


const fetch_differences=(async(req,res)=>{

    const repoName=req.body.repoName;
    const pullNo=req.body.pull_number;

    const response=await axios.get(`https://api.github.com/repos/developranadr18vit25/${repoName}/pulls/${pullNo}/files`);

    return res.json({
        PR_diff:response.data
    })
})

module.exports={
    fetch_differences
}