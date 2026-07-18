
const fetchRepoData=(async(req,res)=>{

    const reponse=await fetch("https://api.github.com/user/repos" , {
        method:"GET",
        headers:{
            Authorization:`Bearer ${token}`,
            Accept: "application/vnd.github+json"
        }
    })

    const repos=await reponse.json();

    res.json(repos);
})

module.exports={
    fetchRepoData
}